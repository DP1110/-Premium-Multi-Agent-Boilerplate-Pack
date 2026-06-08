<![CDATA[<div align="center">

# ⚡ Toolify-API

### Public API → Gemini Tool Converter

**Instantly convert 1,400+ public APIs into Google Gemini-compatible tool schemas and Python function wrappers.**

[![Streamlit](https://img.shields.io/badge/Streamlit-1.32-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-00ffcc)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)

---

</div>

## 🎯 What Is Toolify-API?

Toolify-API is a cloud-hosted web application that reads the [public-apis/public-apis](https://github.com/public-apis/public-apis) GitHub registry and automatically generates:

- **🐍 Python `requests` Wrapper Functions** — Copy-paste-ready functions that call any public API with proper authentication handling, error management, and type hints.
- **🤖 Google Gemini JSON Tool Schemas** — Fully compliant `FunctionDeclaration` objects formatted for the `google-genai` SDK, ready to bind to any Gemini model.
- **⚙️ SDK Integration Snippets** — Drop-in code showing exactly how to wire each tool into `genai.Client().models.generate_content()`.

> **Data Source:** All API data is fetched live from the [public-apis](https://github.com/public-apis/public-apis) open-source registry.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **1,400+ APIs** | Browse the entire public-apis catalog with category filtering |
| **Gemini-Native Schemas** | Output matches `types.FunctionDeclaration` / `types.Schema` format exactly |
| **Zero Config** | No API keys needed for the web app itself |
| **One-Click Copy** | Copy generated Python code or JSON schemas instantly |
| **Premium Agent Demo** | Full autonomous function-calling loop in `premium_agent.py` |
| **Dark Theme** | Custom glassmorphism UI with neon-cyan accents |

---

## 🚀 Quick Start — Local Setup

### Prerequisites

- Python 3.10 or higher
- `pip` package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/toolify-api.git
cd toolify-api

# Install dependencies
pip install -r requirements.txt

# Launch the app
streamlit run app.py
```

The app will open at `http://localhost:8501`.

### Running the Premium Agent

```bash
# Set your Gemini API key
export GEMINI_API_KEY="your-api-key-here"

# Run the autonomous agent demo
python premium_agent.py
```

---

## ☁️ Deploy to Streamlit Community Cloud

Streamlit Community Cloud provides **free hosting** for public Streamlit apps.

### Step-by-Step

1. **Push to GitHub** — Upload this project to a public GitHub repository.

2. **Sign in** — Go to [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account.

3. **Deploy**:
   - Click **"New app"**
   - Select your repository, branch (`main`), and main file path (`app.py`)
   - Click **"Deploy"**

4. **Configure Secrets** *(optional, for the agent module)*:
   - In the Streamlit Cloud dashboard, open **Settings → Secrets**
   - Add:
     ```toml
     GEMINI_API_KEY = "your-api-key-here"
     ```

5. **Done!** — Your app will be live at `https://your-app.streamlit.app`

### Deployment Checklist

- [x] `requirements.txt` with pinned versions
- [x] `.streamlit/config.toml` with theme configuration
- [x] No local file dependencies — data fetched from GitHub
- [x] `st.cache_data` for efficient API calls

---

## 🏗️ Project Structure

```
toolify-web/
├── .streamlit/
│   └── config.toml          # Premium dark theme configuration
├── requirements.txt          # Pinned Python dependencies
├── app.py                    # Core Streamlit web application
├── premium_agent.py          # Gemini autonomous agent runner
└── README.md                 # This file
```

### File Overview

| File | Purpose |
|---|---|
| `config.toml` | Defines the dark theme: neon cyan primary, deep-dark backgrounds |
| `requirements.txt` | Streamlit 1.32, Requests 2.32, Google GenAI 0.4 |
| `app.py` | Fetches APIs, generates Python wrappers + Gemini schemas, renders UI |
| `premium_agent.py` | Class-based agent with tool registry and function-calling loop |

---

## 🤖 How the Gemini Integration Works

### Generated Schema Format

Every API is converted into a Gemini-compatible `FunctionDeclaration`:

```json
{
  "name": "call_cat_facts",
  "description": "Daily cat facts",
  "parameters": {
    "type": "OBJECT",
    "properties": {
      "query": {
        "type": "STRING",
        "description": "Search term or resource identifier."
      }
    },
    "required": ["query"]
  }
}
```

### Autonomous Agent Loop

The `premium_agent.py` module implements the full cycle:

```
User Prompt → Gemini Model → Function Call(s) → Execute HTTP → FunctionResponse → Gemini → Final Answer
```

This loop runs autonomously for up to 10 turns, handling multi-step tool invocations.

---

## 💎 Premium Multi-Agent Boilerplate Pack

> **Level up your AI agent development.**

The Premium Pack includes production-ready templates for:

- 🔄 **Multi-tool orchestration** — Chain multiple API calls in a single agent turn
- 📡 **Streaming responses** — Real-time token streaming with tool interrupts
- 🌐 **Cloud deployment configs** — Docker, Cloud Run, and Railway templates
- 🧪 **Testing harness** — Mock tool execution for unit testing agent logic
- 📊 **Observability** — Built-in logging, token counting, and cost tracking

### 🛒 Get the Premium Pack

| Store | Link |
|---|---|
| **Gumroad** | [toolify.gumroad.com/l/premium-agent-pack](https://toolify.gumroad.com/l/premium-agent-pack) |
| **GitHub Sponsors** | [github.com/sponsors/toolify-api](https://github.com/sponsors/toolify-api) |
| **Ko-fi** | [ko-fi.com/toolifyapi](https://ko-fi.com/toolifyapi) |

---

## 📄 License

This project is released under the [MIT License](LICENSE).

---

<div align="center">

**Built with ♥ using [Streamlit](https://streamlit.io) · Powered by [public-apis](https://github.com/public-apis/public-apis) · Optimized for [Google Gemini](https://ai.google.dev/)**

</div>
]]>
