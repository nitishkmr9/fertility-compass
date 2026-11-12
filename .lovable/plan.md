# Reproductive Potential Monitor

Build a runnable, zero-license-cost local Python app plus a polished preview dashboard, with synthetic data as the only default input.

## Deliverables
- Streamlit clinician dashboard with synthetic personas, longitudinal lab/input trends, missing-data and uncertainty indicators, consent controls, and population summaries that suppress small cohorts.
- Python modules for SQLite persistence with encrypted health payloads, explicit/revocable per-category consent, audit events, purpose restrictions, guideline-grounded retrieval, and constrained LangGraph/Ollama interpretation that never produces a fertility score or diagnosis.
- Synthetic demo personas, bundled source references, safety/privacy/evaluation tests, setup instructions, and a Microsoft Foundry migration map that does not introduce Azure dependencies.
- Replace the template home screen with a responsive, interactive synthetic-data preview of the monitoring workflow.

## Safety boundaries
- Local-only research/demo use; no authentication, real-patient deployment claim, deterministic fertility score, diagnosis, treatment protocol, or unsupported guideline claim.
- Inputs require active granular consent; missing evidence blocks clinical interpretation, and employment/insurance purposes are denied and audited.
- Use established professional guideline references and visible citations; disclose the limitations of bundled evidence, synthetic population data, and local encryption key handling.

## Implementation notes
- Keep the Python app isolated in `fertility-agent/` so it can run with `pip install -e .` and `streamlit run app.py` without changing the Lovable frontend toolchain.
- Put durable architectural rules in the root `AGENTS.md`; keep Python tests adjacent to the deliverable and run them before completion.
