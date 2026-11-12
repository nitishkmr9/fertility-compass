from __future__ import annotations

import json
import re
from typing import Any, TypedDict

from .guidelines import ALLOWED_OPTIONS


class MonitoringState(TypedDict, total=False):
    query: str
    observations: list[dict[str, Any]]
    missing_data: list[str]
    retrieved: list[dict[str, Any]]
    answer: dict[str, Any]
    model_name: str


def make_change_summary(observations: list[dict[str, Any]]) -> list[str]:
    """Describe like-for-like measurements only; never assign a clinical meaning."""
    samples: dict[tuple[str, str], list[tuple[str, float]]] = {}
    for observation in observations:
        for scope, entries in observation.get("data", {}).items():
            if scope != "labs" or not isinstance(entries, list):
                continue
            for result in entries:
                name = str(result.get("name", "")).strip().upper()
                unit = str(result.get("unit", "")).strip()
                value = result.get("value")
                if name and unit and isinstance(value, (int, float)):
                    samples.setdefault((name, unit), []).append((observation["occurred_at"], float(value)))
    summaries = []
    for (name, unit), values in sorted(samples.items()):
        values.sort(key=lambda entry: entry[0])
        if len(values) < 2:
            continue
        first, last = values[0][1], values[-1][1]
        direction = "no change" if first == last else "increased" if last > first else "decreased"
        summaries.append(f"{name} {direction}: {first:g} to {last:g} {unit} across {len(values)} entries; direction only, not a prediction.")
    return summaries


def validate_and_limit_output(raw: str, retrieved: list[dict[str, Any]]) -> dict[str, Any]:
    """Allow only enumerated options and citations that are actually retrieved."""
    known_ids = {item["id"] for item in retrieved}
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return {"status": "blocked", "options": [], "citations": [], "notice": "Interpretation unavailable: response format was not verifiable."}

    if not isinstance(parsed, dict):
        return {"status": "blocked", "options": [], "citations": [], "notice": "Interpretation unavailable: response format was not verifiable."}
    options = parsed.get("options", [])
    citations = parsed.get("citations", [])
    note = parsed.get("note", "")
    if (
        not isinstance(options, list)
        or any(option not in ALLOWED_OPTIONS for option in options)
        or not isinstance(citations, list)
        or any(citation not in known_ids for citation in citations)
        or not isinstance(note, str)
        or re.search(r"\b(?:fertility score|diagnos(?:is|e)|pregnancy probability|will conceive)\b", note, re.I)
    ):
        return {"status": "blocked", "options": [], "citations": [], "notice": "Interpretation withheld: it did not meet evidence and safety checks."}
    return {
        "status": "grounded",
        "options": list(dict.fromkeys(options)),
        "citations": list(dict.fromkeys(citations)),
        "notice": note,
    }


def run_monitoring_workflow(query: str, observations: list[dict[str, Any]], missing_data: list[str], retriever: Any, model_name: str = "qwen3:4b") -> dict[str, Any]:
    """Run Chroma evidence retrieval then a bounded local Ollama response."""
    try:
        from langchain_ollama import ChatOllama
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise RuntimeError("Install the project requirements to use LangGraph with Ollama") from exc

    def retrieve(state: MonitoringState) -> dict[str, Any]:
        return {"retrieved": retriever.search(state["query"], limit=4)}

    def generate(state: MonitoringState) -> dict[str, Any]:
        evidence = state.get("retrieved", [])
        if not evidence:
            return {"answer": {"status": "blocked", "options": [], "citations": [], "notice": "No cited guideline text was found. No interpretation is available."}}
        permitted = ["Lifestyle optimization", "Testing", "Preconception counselling", "Fertility-preservation discussion", "Specialist referral"]
        prompt = (
            "You are an educational summarizer, not a clinician. Do not diagnose, predict pregnancy, rank fertility, "
            "alarm, or prescribe. Return JSON ONLY with keys options, citations, note. options must be a list of "
            "zero or more strings from this exact list: " + json.dumps(permitted) + ". citations must contain only provided IDs. "
            "Every factual claim in note must be directly supported by supplied evidence and cited by ID; otherwise use an empty note. "
            "Select only cautious discussion options supported by the context, never treatments. State that missing data and uncertainty limit interpretation. "
            "Inputs can be sensitive; never repeat record values. User request: " + state["query"] + "\n"
            "Missing categories: " + json.dumps(state.get("missing_data", [])) + "\n"
            "Descriptive trends only: " + json.dumps(make_change_summary(state.get("observations", []))) + "\n"
            "Retrieved evidence: " + json.dumps(evidence, ensure_ascii=False)
        )
        message = ChatOllama(model=state["model_name"], temperature=0).invoke(prompt)
        raw = message.content if isinstance(message.content, str) else ""
        return {"answer": validate_and_limit_output(raw, evidence)}

    graph = StateGraph(MonitoringState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    result = graph.compile().invoke({
        "query": query,
        "observations": observations,
        "missing_data": missing_data,
        "retrieved": [],
        "model_name": model_name,
    })
    return result["answer"]