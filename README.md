# Toolify-API — Premium Multi-Agent Boilerplate Pack

Converted the public-apis registry into structured Gemini JSON Tool Schemas, Python `requests` wrappers, and multi-SDK integration snippets for Gemini, OpenAI, Claude, and Ollama. Built with Streamlit.

[Live demo • Toolify-API (Streamlit)](https://toolify-api.streamlit.app/)

---

## Overview

Toolify-API reads entries from the public-apis registry and generates:

- Gemini-compatible JSON Tool Schemas (FunctionDeclaration objects) for each API
- Lightweight Python `requests` wrappers with sensible defaults and type hints
- Integration snippets showing how to register/use the same tool with multiple LLM SDKs (Google Gemini, OpenAI, Anthropic/Claude, Ollama)
- A Streamlit demo app to explore generated schemas and try API calls interactively

This repository includes a premium multi-agent boilerplate demonstrating autonomous tool-calling loops and production-ready agent patterns.

---

## Live demo

Try the hosted Streamlit demo and API examples:

- Streamlit app: https://toolify-api.streamlit.app/

---

## Quick start

1. Clone this repository:

```bash
git clone https://github.com/DP1110/-Premium-Multi-Agent-Boilerplate-Pack.git
cd -Premium-Multi-Agent-Boilerplate-Pack
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate    # macOS / Linux
.\.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

3. Run the Streamlit demo locally:

```bash
streamlit run app.py
```

The app will open at http://localhost:8501 by default.

---

## Usage examples

- Call a generated Python wrapper:

```python
from api_wrappers.cat_facts import get_cat_facts
print(get_cat_facts(limit=5))
```

- Use the Gemini/FunctionDeclaration schemas with a Gemini-capable SDK to register tools and let models call them.

See the `examples/` folder for provider-specific snippets.

---

## Project structure (high level)

- app.py — Streamlit web UI and generator
- premium_agent.py — Example autonomous agent using the generated tool registry
- api_wrappers/ — Generated Python wrappers per API
- schemas/ — Generated Gemini JSON Tool Schemas
- requirements.txt — Python dependencies

---

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (public repo).
2. Go to https://share.streamlit.io and click "New app".
3. Select this repository, the branch (default), and `app.py` as the main file.

Optional: add secrets (e.g., GEMINI_API_KEY) in the Streamlit dashboard if you plan to run the premium agent.

---

## License

This project includes an MIT License file (see LICENSE).

---

## Contact

Repository: https://github.com/DP1110/-Premium-Multi-Agent-Boilerplate-Pack
Streamlit demo / API examples: https://toolify-api.streamlit.app/

---

Made with Streamlit. README updated by GitHub Copilot on behalf of the repository owner.
