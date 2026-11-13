from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
DATA_DIR = Path(os.environ.get("FERTILITY_DATA_DIR", ROOT / ".data")).expanduser()
sys.path.insert(0, str(ROOT))

from fertility_agent.demo import seed_demo_personas  # noqa: E402
from fertility_agent.guidelines import SOURCES  # noqa: E402
from fertility_agent.rag import GuidelineRetriever  # noqa: E402
from fertility_agent.security import load_cipher, new_anonymous_id  # noqa: E402
from fertility_agent.storage import SCOPES, SCOPE_LABELS, LocalStore  # noqa: E402
from fertility_agent.workflow import make_change_summary, run_monitoring_workflow  # noqa: E402

st.set_page_config(page_title="Tide · Reproductive health trends", page_icon="◌", layout="wide", initial_sidebar_state="expanded")


@st.cache_resource
def get_store() -> LocalStore:
    return LocalStore(DATA_DIR / "monitor.sqlite3", load_cipher(DATA_DIR / "local.key"))


def list_to_text(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


store = get_store()
seed_demo_personas(store)

st.title("Tide")
st.caption("REPRODUCTIVE HEALTH · PRIVATE BY DESIGN")
st.info("Local research demo · Use fictional data only · Not for diagnosis, prediction, employment, or insurance decisions.", icon="◌")

view = st.sidebar.radio("Workspace", ["Overview", "People", "Cohort insights", "Guidelines", "Audit log"], label_visibility="visible")
st.sidebar.divider()
st.sidebar.caption("FICTIONAL DEMO RECORDS")
participants = store.list_participants()
if not participants:
    st.error("No demo records are available. Restart the app to create its synthetic examples.")
    st.stop()
names = {person["display_name"]: person["participant_id"] for person in participants}
selected_name = st.sidebar.selectbox("Selected record", list(names))
participant_id = names[selected_name]
selected = next(person for person in participants if person["participant_id"] == participant_id)

if view == "Overview":
    st.subheader(f"{selected_name}", anchor=False)
    st.caption("Synthetic patient profile · longitudinal view · no clinical risk classification")
    observation_rows = store.observations_for(participant_id)
    consent = store.consent_for(participant_id)
    age = next((row["data"].get("profile", {}).get("age") for row in observation_rows if "profile" in row["data"]), None)
    lab_count = sum(len(row["data"].get("labs", {}).get("results", [])) for row in observation_rows)
    last_updated = observation_rows[-1]["occurred_at"][:10] if observation_rows else "No saved entries"
    metrics = st.columns(4)
    metrics[0].metric("AGE AT LAST ENTRY", f"{age} years" if age is not None else "Not shared")
    metrics[1].metric("RECORDED VISITS", str(len(observation_rows)))
    metrics[2].metric("LAB RESULTS", str(lab_count), help="Count only; no interpretation or individual fertility score.")
    metrics[3].metric("LAST ENTRY", last_updated)

    chart_area, options_area = st.columns([1.65, 1], gap="large")
    with chart_area:
        st.markdown("### Change over time")
        lab_series: dict[str, list[dict[str, object]]] = {}
        for observation in observation_rows:
            for result in observation["data"].get("labs", {}).get("results", []):
                key = f"{result.get('name', 'Lab')} · {result.get('unit', 'unit not recorded')}"
                lab_series.setdefault(key, []).append({"Date": observation["occurred_at"][:10], "Value": result.get("value")})
        chart_selection = st.selectbox("View lab history", ["All entries", *lab_series.keys()], label_visibility="collapsed") if lab_series else None
        chosen = {chart_selection: lab_series[chart_selection]} if chart_selection in lab_series else lab_series
        plot_data = pd.DataFrame([
            {"Date": point["Date"], "Value": point["Value"], "Test": test_name}
            for test_name, points in chosen.items() for point in points
        ])
        if plot_data.empty:
            st.markdown('<div class="empty-plot">Your selected record has no repeat lab results to chart.</div>', unsafe_allow_html=True)
        else:
            plot_data["Date"] = pd.to_datetime(plot_data["Date"])
            st.line_chart(plot_data, x="Date", y="Value", color="Test", height=255, use_container_width=True)
        st.caption("Recorded values and direction only. Tests, units, timing and lab methods can differ; this does not show fertility or predict pregnancy.")

    with options_area:
        st.markdown("### Record completeness")
        for scope, label in SCOPE_LABELS.items():
            present = consent.get(scope, False) and any(scope in row["data"] for row in observation_rows)
            status = "Recorded" if present else "Not shared"
            st.markdown(f"<div class='scope-row'><span>{label}</span><span class='scope-status'>{status}</span></div>", unsafe_allow_html=True)
        st.markdown("### Guideline-grounded notes")
        trend_notes = make_change_summary(observation_rows)
        if trend_notes:
            for note in trend_notes[:3]:
                st.markdown(f"<div class='note-line'>{note}</div>", unsafe_allow_html=True)
        else:
            st.caption("No comparable repeated lab values are available for a direction-of-change summary.")
        st.caption("No diagnosis, clinical threshold, or fertility score is generated.")

    st.divider()
    st.markdown("### Evidence & next conversation")
    st.caption("Only a clinician can assess these records in context. Optional conversations—not automated instructions:")
    opt_cols = st.columns(5)
    for column, option in zip(opt_cols, ["Lifestyle optimization", "Testing", "Preconception counselling", "Fertility-preservation discussion", "Specialist referral"], strict=True):
        column.markdown(f"<div class='option-note'>{option}</div>", unsafe_allow_html=True)
    st.caption("Choose a topic to discuss with a qualified clinician; nothing here recommends testing or care.")

    st.markdown("### Guideline library")
    with st.expander("View named references and limitations"):
        for source in SOURCES:
            st.markdown(f"**{source.publisher} · {source.title} ({source.published})** · [Open source]({source.url})")
            st.caption(source.review_note)

elif view == "People":
    st.subheader("People & permissions")
    st.caption("Demo entries are fictional. A local anonymous record can be added only after category-by-category consent.")
    with st.form("new_local_record"):
        age_consent = st.checkbox("I consent to save age and profile details.")
        history_consent = st.checkbox("I consent to save reproductive history.")
        lifestyle_consent = st.checkbox("I consent to save lifestyle notes.")
        conditions_consent = st.checkbox("I consent to save health-condition notes.")
        labs_consent = st.checkbox("I consent to save clinician-entered lab values.")
        device_consent = st.checkbox("I consent to save optional device notes.")
        age_value = st.number_input("Age in years", min_value=18, max_value=100, value=32)
        history_note = st.text_input("Reproductive history notes", max_chars=160)
        lifestyle_note = st.text_input("Lifestyle notes", max_chars=160)
        conditions_note = st.text_input("Health condition notes", max_chars=160)
        lab_name = st.selectbox("Clinician-entered lab name", ["AMH", "FSH", "TSH"])
        lab_value = st.number_input("Lab value (as reported)", min_value=0.0, value=0.0, step=0.1)
        lab_unit = st.text_input("Lab unit", max_chars=24, placeholder="As reported by the lab")
        device_note = st.text_input("Device note (optional; manually entered)", max_chars=160)
        purpose = st.selectbox("Purpose", ["Care", "Employment", "Insurance"], disabled=False)
        save = st.form_submit_button("Save consented record")
        if save:
            if purpose != "Care":
                try:
                    store.save_observation("new-record", date.today().isoformat(), {"profile": {"age": age_value}}, purpose=purpose)
                except PermissionError as exc:
                    st.error(str(exc))
            else:
                authorized = {
                    "profile": (age_consent, {"age": age_value}),
                    "history": (history_consent, {"notes": history_note}),
                    "lifestyle": (lifestyle_consent, {"notes": lifestyle_note}),
                    "conditions": (conditions_consent, {"notes": conditions_note}),
                    "labs": (labs_consent, {"results": [{"name": lab_name, "value": lab_value, "unit": lab_unit}]}) if lab_unit.strip() else (False, {}),
                    "device_data": (device_consent, {"notes": device_note}),
                }
                scoped = {scope: data for scope, (is_granted, data) in authorized.items() if is_granted}
                if not scoped:
                    st.error("Nothing was saved. Select consent only for the categories you want to store.")
                elif any(scope == "labs" and not lab_unit.strip() for scope in authorized if authorized[scope][0]):
                    st.error("Enter the lab's reported unit or leave lab data unselected.")
                else:
                    anonymous_id = new_anonymous_id()
                    store.add_participant(anonymous_id, f"Local record {anonymous_id[:5]}")
                    store.set_consent(anonymous_id, [scope for scope, (enabled, _) in authorized.items() if enabled], True)
                    try:
                        store.save_observation(anonymous_id, date.today().isoformat(), scoped)
                    except (PermissionError, ValueError, sqlite3.Error) as exc:
                        store.set_consent(anonymous_id, SCOPES, False)
                        st.error(f"The record was not saved: {exc}")
                    else:
                        st.success("The consented local record was saved.")

    st.divider()
    st.markdown("### Revoke consent & erase a category")
    revoke_scope = st.selectbox("Category to revoke", SCOPES, format_func=lambda scope: SCOPE_LABELS[scope])
    if st.button("Revoke and erase saved values"):
        store.set_consent(participant_id, [revoke_scope], False)
        st.success(f"Consent revoked; stored {SCOPE_LABELS[revoke_scope].lower()} were erased from this record.")

elif view == "Cohort insights":
    st.subheader("Synthetic population insights")
    st.caption("Fictional demo records only · no clinical outcomes · no protected records enter aggregates")
    summaries = store.participant_summaries()
    summary = summaries[0]
    if summary["suppressed"]:
        st.info("Cohort is below the minimum size for safe aggregate display. No number is shown.")
    else:
        st.metric("Synthetic example records", summary["count"])
    category_counts = {scope: 0 for scope in SCOPES}
    for person in participants:
        if not person["synthetic"]:
            continue
        for item in store.observations_for(person["participant_id"]):
            for scope in item["data"]:
                category_counts[scope] += 1
    st.markdown("### Recorded categories · synthetic examples")
    st.bar_chart(pd.DataFrame({"Entries": category_counts.values()}, index=[SCOPE_LABELS[key] for key in category_counts]), horizontal=True)
    st.caption("Counts are descriptive, not prevalence estimates. Cohorts smaller than five are suppressed; only fictional records are included.")

elif view == "Guidelines":
    st.subheader("Evidence library")
    st.caption("Public professional guidance · summaries are for educational context, not medical advice.")
    for source in SOURCES:
        st.markdown(f"#### {source.publisher} · {source.title}")
        st.caption(f"{source.published} · source reviewed at publication; verify for updates")
        st.write(source.summary)
        st.caption(source.review_note)
        st.link_button("Open official guidance", source.url)

elif view == "Audit log":
    st.subheader("Local audit trail")
    st.caption("Consent changes, blocked purposes and saves are recorded locally. No patient-entered text appears in this log.")
    events = store.audit_events()
    if events:
        st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)
    else:
        st.caption("No activity recorded yet.")

st.sidebar.divider()
st.sidebar.caption("Local-only mode · manual entries · no external data connections")
with st.sidebar.expander("Ask about the selected history"):
    prompt = st.text_area("Educational question", placeholder="What can these trends tell us?", max_chars=500)
    if st.button("Search guidelines", use_container_width=True):
        if not prompt.strip():
            st.warning("Enter a question first.")
        else:
            with st.spinner("Searching local guideline references…"):
                try:
                    retriever = GuidelineRetriever(DATA_DIR / "chroma")
                    observations = store.observations_for(participant_id)
                    all_scopes = store.consent_for(participant_id)
                    missing = [label for scope, label in SCOPE_LABELS.items() if not all_scopes[scope]]
                    answer = run_monitoring_workflow(prompt, observations, missing, retriever)
                except Exception as exc:
                    answer = {"status": "blocked", "citations": [], "options": [], "notice": f"No interpretation is available. Confirm Ollama and the selected local model are running. ({type(exc).__name__})"}
            st.markdown(f"**Status:** {answer['status']}")
            st.write(answer["notice"])
            if answer.get("options"):
                st.write("Discussion topics:", ", ".join(answer["options"]))
            for citation in answer.get("citations", []):
                source = next((item for item in SOURCES if item.source_id == citation), None)
                if source:
                    st.markdown(f"Source: [{source.publisher} · {source.title} ({source.published})]({source.url})")

st.divider()
st.caption("Use fictional data only. This prototype is not a medical device; does not diagnose, predict fertility or provide treatment; and must never support employment or insurance decisions. A human clinician must interpret test results and advise care.")