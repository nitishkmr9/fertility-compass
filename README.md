# Fertility Compass

Build a zero-cost fertility "reproductive potential" monitoring agent (Python + Streamlit + LangGraph + Ollama/local LLM + ChromaDB RAG + SQLite, no Azure). It tracks AUTHORIZED inputs only (age, history, lifestyle, conditions, labs like AMH/FSH/TSH, device data) and shows DIRECTION OF CHANGE over time — never a deterministic "fertility score." RAG-ground every interpretation in ASRM/ESHRE/WHO/NICE guidelines and cite them; explicitly state missing data and uncertainty. Classify factors as modifiable/non-modifiable. Output only appropriate options: lifestyle optimization, testing, preconception counselling, fertility-preservation discussion, or specialist referral. Include: clinician dashboard, population-level anonymized insights, granular revocable consent, encryption, audit logs, blocks on using reproductive data for employment/insurance, and a Responsible-AI eval harness (hallucination, alarmist tone, bias, privacy leaks). Deliver a full runnable repo with synthetic demo personas and a README mapping each component to Microsoft Foundry (agents, AI Search, model deployment, Responsible AI, MCP tools) so it can be ported to Azure later.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/c8076a63-f84c-4f88-8d8b-7bf69be48297).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
