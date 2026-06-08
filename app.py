"""
Toolify-API — Public API → Gemini Tool Converter
==================================================
Converts entries from the public-apis GitHub registry into:
  • Executable Python `requests` wrapper functions
  • Google Gemini-compatible JSON tool-function declaration schemas

Data source: https://github.com/public-apis/public-apis
"""

import json
import re
import textwrap

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Toolify-API · Public API → Gemini Tool Converter",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Injected CSS — premium glassmorphism / gradient / micro-animation theme
# ---------------------------------------------------------------------------
st.markdown(
    '<meta name="referrer" content="no-referrer">',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ---------- globals ---------- */
    html, body, .stApp, .stApp * {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: linear-gradient(160deg, #0d1117 0%, #10171e 40%, #0d1117 100%);
    }

    /* ---------- scrollbar ---------- */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #00ffcc44; border-radius: 3px; }

    /* ---------- CTA banner ---------- */
    .cta-banner {
        background: linear-gradient(135deg, #00ffcc15, #7928ca18, #ff008015);
        border: 1px solid #00ffcc30;
        border-radius: 16px;
        padding: 28px 36px;
        margin-bottom: 28px;
        backdrop-filter: blur(12px);
        position: relative;
        overflow: hidden;
        animation: bannerGlow 4s ease-in-out infinite alternate;
    }
    .cta-banner::before {
        content: '';
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: radial-gradient(circle at 30% 50%, #00ffcc08, transparent 60%);
        animation: rotateBg 12s linear infinite;
    }
    @keyframes bannerGlow {
        0%   { box-shadow: 0 0 20px #00ffcc10; }
        100% { box-shadow: 0 0 40px #7928ca18; }
    }
    @keyframes rotateBg {
        100% { transform: rotate(360deg); }
    }
    .cta-banner h2 {
        margin: 0 0 6px 0;
        font-size: 1.35rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00ffcc, #7928ca, #ff0080);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        position: relative;
    }
    .cta-banner p {
        color: #8b949e;
        margin: 0 0 14px 0;
        font-size: 0.92rem;
        position: relative;
    }
    .cta-btn {
        display: inline-block;
        background: linear-gradient(135deg, #00ffcc, #7928ca);
        color: #0d1117 !important;
        font-weight: 700;
        padding: 10px 28px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 0.9rem;
        transition: transform 0.2s, box-shadow 0.2s;
        position: relative;
    }
    .cta-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px #00ffcc30;
    }

    /* ---------- glass cards ---------- */
    .glass-card {
        background: #161b2280;
        border: 1px solid #30363d;
        border-radius: 14px;
        padding: 22px 26px;
        backdrop-filter: blur(10px);
        margin-bottom: 18px;
        transition: border-color 0.3s, box-shadow 0.3s;
    }
    .glass-card:hover {
        border-color: #00ffcc50;
        box-shadow: 0 0 18px #00ffcc12;
    }
    .glass-card h3 {
        margin: 0 0 12px 0;
        font-size: 1.05rem;
        color: #e6edf3;
        font-weight: 600;
    }

    /* ---------- meta badges ---------- */
    .meta-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
    .meta-badge {
        display: inline-flex; align-items: center; gap: 5px;
        background: #21262d;
        border: 1px solid #30363d;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.78rem;
        color: #8b949e;
        font-weight: 500;
        transition: border-color 0.2s;
    }
    .meta-badge:hover { border-color: #00ffcc60; }
    .meta-badge .dot {
        width: 7px; height: 7px;
        border-radius: 50%;
        display: inline-block;
    }
    .dot-green  { background: #3fb950; }
    .dot-yellow { background: #d29922; }
    .dot-red    { background: #f85149; }
    .dot-blue   { background: #58a6ff; }

    /* ---------- section headers ---------- */
    .section-hdr {
        display: flex; align-items: center; gap: 8px;
        margin: 0 0 10px 0;
        font-size: 0.85rem;
        font-weight: 600;
        color: #00ffcc;
        text-transform: uppercase;
        letter-spacing: 1.2px;
    }

    /* ---------- source link ---------- */
    .source-link {
        text-align: center;
        padding: 10px 0 20px 0;
        font-size: 0.82rem;
        color: #8b949e;
    }
    .source-link a {
        color: #00ffcc;
        text-decoration: none;
        font-weight: 600;
        transition: color 0.2s;
    }
    .source-link a:hover { color: #7928ca; }

    /* ---------- sidebar ---------- */
    section.stSidebar {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
        border-right: 1px solid #21262d;
    }
    section.stSidebar .stSelectbox label {
        color: #8b949e;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    /* ---------- code blocks ---------- */
    .stCodeBlock { border-radius: 12px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

def clean_url(url_str: str) -> str:
    """Strip UTM parameters and tracking tags from a URL to avoid firewall blocks."""
    if not url_str:
        return ""
    try:
        u = urlparse(url_str)
        q = parse_qsl(u.query)
        q_clean = [(k, v) for k, v in q if not k.startswith('utm_')]
        query_clean = urlencode(q_clean)
        return urlunparse((u.scheme, u.netloc, u.path, u.params, query_clean, u.fragment))
    except Exception:
        return url_str


README_URL = (
    "https://raw.githubusercontent.com/public-apis/public-apis"
    "/master/README.md"
)


@st.cache_data(show_spinner="Fetching and parsing public API registry …", ttl=3600)
def load_api_registry() -> list[dict]:
    """Download the public-apis README.md and parse the markdown tables."""
    try:
        response = requests.get(README_URL, timeout=30)
        response.raise_for_status()
    except Exception as e:
        st.error(f"Failed to fetch public-apis README.md: {e}")
        return []

    entries = []
    current_category = None
    link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    
    lines = response.text.split("\n")
    for line in lines:
        line_str = line.strip()
        if line_str.startswith("### "):
            current_category = line_str[4:].strip()
            continue
            
        if current_category and "|" in line_str:
            # Check if it's a separator or header row
            if "API | Description" in line_str or "|:---" in line_str:
                continue
            
            # Split columns
            parts = [p.strip() for p in line_str.split("|")]
            # Table lines start and end with |, so parts[0] and parts[-1] might be empty
            if parts and not parts[0]:
                parts.pop(0)
            if parts and not parts[-1]:
                parts.pop()
                
            if len(parts) >= 5:
                api_markdown = parts[0]
                description = parts[1]
                auth = parts[2].replace("`", "").strip()
                if auth.lower() in ("no", "none", ""):
                    auth = ""
                https_str = parts[3].lower()
                https = True if "yes" in https_str else False
                cors = parts[4].replace("`", "").strip()
                
                # Parse API link
                match = link_re.search(api_markdown)
                if match:
                    api_name = match.group(1).strip()
                    api_link = clean_url(match.group(2).strip())
                else:
                    api_name = api_markdown.strip()
                    api_link = ""
                    
                entries.append({
                    "API": api_name,
                    "Description": description,
                    "Auth": auth,
                    "HTTPS": https,
                    "Cors": cors,
                    "Link": api_link,
                    "Category": current_category
                })
                
    return entries



# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
def sanitize_name(raw: str) -> str:
    """Convert an API name into a valid Python / tool identifier."""
    name = re.sub(r"[^a-zA-Z0-9]+", "_", raw.strip()).strip("_").lower()
    if name and name[0].isdigit():
        name = f"api_{name}"
    return name or "unnamed_api"


def generate_python_wrapper(api: dict) -> str:
    """Build an executable Python `requests` wrapper function string."""
    func_name = f"call_{sanitize_name(api.get('API', 'unknown'))}"
    link = api.get("Link", "https://example.com")
    auth = api.get("Auth", "")
    description = api.get("Description", "No description available.")
    https = api.get("HTTPS", True)

    headers_block = ""
    params_sig = ""
    params_doc = ""
    if auth and auth.lower() not in ("", "no"):
        headers_block = (
            '    headers = {"Authorization": f"Bearer {api_key}"}\n'
        )
        params_sig = "api_key: str, "
        params_doc = (
            "        api_key: Authentication key/token for the API.\n"
        )

    protocol = "https" if https else "http"
    # Normalise the link — ensure it starts with a protocol
    base_url = link if link.startswith("http") else f"{protocol}://{link}"

    code = f"""\
import requests


def {func_name}({params_sig}query: str = "") -> dict:
    \"\"\"
    {description}

    Args:
{params_doc}        query: Search term or resource identifier.

    Returns:
        dict: JSON response from the API.
    \"\"\"
    url = "{base_url}"
    params = {{"q": query}} if query else {{}}
{headers_block}    response = requests.get(
        url,
        params=params,
{"        headers=headers," if headers_block else ""}
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
"""
    return code


def generate_gemini_schema(api: dict) -> dict:
    """Build a Google Gemini-compatible FunctionDeclaration dict."""
    func_name = f"call_{sanitize_name(api.get('API', 'unknown'))}"
    description = api.get("Description", "No description available.")
    auth = api.get("Auth", "")

    properties: dict = {
        "query": {
            "type": "STRING",
            "description": (
                "Search term or resource identifier to send to the API."
            ),
        },
    }
    required = ["query"]

    if auth and auth.lower() not in ("", "no"):
        properties["api_key"] = {
            "type": "STRING",
            "description": "Authentication key or token for the API.",
        }
        required.append("api_key")

    schema = {
        "name": func_name,
        "description": description,
        "parameters": {
            "type": "OBJECT",
            "properties": properties,
            "required": required,
        },
    }
    return schema


# ---------------------------------------------------------------------------
# Premium CTA Banner
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="cta-banner">
        <h2>🚀 Premium Multi-Agent Boilerplate Pack</h2>
        <p style="margin-bottom: 16px;">
            Production-ready autonomous agent templates powered by Gemini&nbsp;2.5&nbsp;Flash.
            Includes function-calling loops, multi-tool orchestration, streaming,
            and cloud deployment configs.
        </p>
        <a href="https://github.com/DP1110/-Premium-Multi-Agent-Boilerplate-Pack" target="_blank" class="cta-btn">
            Get the Boilerplate Pack →
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
entries = load_api_registry()

if not entries:
    st.error("⚠️ Could not load the public API registry. Please try again later.")
    st.stop()

# ---------------------------------------------------------------------------
# Source attribution
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="source-link">
        📦 Data sourced from
        <a href="https://github.com/public-apis/public-apis" target="_blank">
            public-apis/public-apis
        </a>
        &nbsp;·&nbsp; {count:,} APIs indexed
    </div>
    """.format(count=len(entries)),
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar — Filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        "<div style='padding:8px 0 18px 0;'>"
        "<span style='font-size:1.4rem;font-weight:800;"
        "background:linear-gradient(90deg,#00ffcc,#7928ca);-webkit-background-clip:text;"
        "-webkit-text-fill-color:transparent;'>⚡ Toolify-API</span></div>",
        unsafe_allow_html=True,
    )

    categories = sorted({e.get("Category", "Uncategorized") for e in entries})
    selected_category = st.selectbox(
        "CATEGORY",
        options=["All Categories"] + categories,
        index=0,
    )

    if selected_category == "All Categories":
        filtered = entries
    else:
        filtered = [
            e for e in entries if e.get("Category") == selected_category
        ]

    api_names = [e.get("API", "Unknown") for e in filtered]
    default_idx = 0
    if "Cat Facts" in api_names:
        default_idx = api_names.index("Cat Facts")
    selected_api_name = st.selectbox("API", options=api_names, index=default_idx)

    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.75rem;color:#484f58;'>"
        f"Showing <strong style='color:#00ffcc'>{len(filtered)}</strong> "
        f"of {len(entries)} APIs</p>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Resolve selected API entry
# ---------------------------------------------------------------------------
selected_api: dict = next(
    (e for e in filtered if e.get("API") == selected_api_name),
    filtered[0] if filtered else {},
)

if not selected_api:
    st.warning("No API selected.")
    st.stop()

# ---------------------------------------------------------------------------
# Main content — two-column layout
# ---------------------------------------------------------------------------
col_left, col_right = st.columns(2, gap="large")

# ---- Column 1: Metadata + Python wrapper ----
with col_left:
    # Metadata card
    auth_raw = selected_api.get("Auth", "")
    auth_label = auth_raw if auth_raw else "None"
    auth_dot = "dot-green" if not auth_raw else "dot-yellow"

    https_val = selected_api.get("HTTPS", False)
    https_label = "Yes" if https_val else "No"
    https_dot = "dot-green" if https_val else "dot-red"

    cors_raw = selected_api.get("Cors", "unknown")
    cors_label = cors_raw if cors_raw else "Unknown"
    cors_dot = (
        "dot-green"
        if cors_raw == "yes"
        else ("dot-red" if cors_raw == "no" else "dot-yellow")
    )

    link = selected_api.get("Link", "#")
    category = selected_api.get("Category", "—")

    st.markdown(
        f"""
        <div class="glass-card">
            <h3>📋 {selected_api.get("API", "Unknown API")}</h3>
            <p style="color:#8b949e;font-size:0.88rem;margin:0 0 14px 0;">
                {selected_api.get("Description", "")}
            </p>
            <div class="meta-row">
                <span class="meta-badge"><span class="dot {auth_dot}"></span>Auth: {auth_label}</span>
                <span class="meta-badge"><span class="dot {https_dot}"></span>HTTPS: {https_label}</span>
                <span class="meta-badge"><span class="dot {cors_dot}"></span>CORS: {cors_label}</span>
                <span class="meta-badge"><span class="dot dot-blue"></span>{category}</span>
            </div>
            <a href="{link}" target="_blank" rel="noopener noreferrer"
               style="color:#00ffcc;font-size:0.82rem;text-decoration:none;font-weight:600;display:inline-block;margin-bottom:6px;">
                🔗 Open API Documentation →
            </a>
            <p style="color:#8b949e;font-size:0.72rem;margin:6px 0 0 0;line-height:1.35;">
                ⚠️ <em>Note: Some third-party API documentation servers block requests or return CloudFront 403 errors based on regional firewalls.</em>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Python wrapper
    st.markdown(
        '<div class="section-hdr">🐍&nbsp; Python Requests Wrapper</div>',
        unsafe_allow_html=True,
    )
    python_code = generate_python_wrapper(selected_api)
    st.code(python_code, language="python")

# ---- Column 2: Gemini schema ----
with col_right:
    st.markdown(
        '<div class="section-hdr">🤖&nbsp; Gemini Tool Declaration Schema</div>',
        unsafe_allow_html=True,
    )
    schema = generate_gemini_schema(selected_api)
    schema_json = json.dumps(schema, indent=2)
    st.code(schema_json, language="json")

    # Integration snippet
    st.markdown(
        '<div class="section-hdr">⚙️&nbsp; SDK Integration Snippet</div>',
        unsafe_allow_html=True,
    )
    
    func_name = sanitize_name(selected_api.get("API", "unknown"))
    api_name = selected_api.get("API", "Unknown")
    api_desc = selected_api.get("Description", "No description available.")
    
    tab_gemini, tab_openai, tab_claude, tab_ollama = st.tabs(["Gemini", "OpenAI", "Claude", "Ollama"])
    
    with tab_gemini:
        gemini_code = textwrap.dedent(f"""\
            from google import genai
            from google.genai import types

            client = genai.Client()

            tool_declaration = types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="call_{func_name}",
                        description={json.dumps(api_desc)},
                        parameters=types.Schema(
                            type="OBJECT",
                            properties={{
                                "query": types.Schema(
                                    type="STRING",
                                    description="Search term or resource identifier.",
                                ),
                            }},
                            required=["query"],
                        ),
                    ),
                ]
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents="Find information using the {api_name} API.",
                config=types.GenerateContentConfig(
                    tools=[tool_declaration],
                ),
            )
            print(response.text)
        """)
        st.code(gemini_code, language="python")
        
    with tab_openai:
        openai_code = textwrap.dedent(f"""\
            import openai

            client = openai.OpenAI()

            tools = [
                {{
                    "type": "function",
                    "function": {{
                        "name": "call_{func_name}",
                        "description": {json.dumps(api_desc)},
                        "parameters": {{
                            "type": "object",
                            "properties": {{
                                "query": {{
                                    "type": "string",
                                    "description": "Search term or resource identifier."
                                }}
                            }},
                            "required": ["query"]
                        }}
                    }}
                }}
            ]

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {{"role": "user", "content": "Find information using the {api_name} API."}}
                ],
                tools=tools,
            )
            print(response.choices[0].message)
        """)
        st.code(openai_code, language="python")
        
    with tab_claude:
        claude_code = textwrap.dedent(f"""\
            import anthropic

            client = anthropic.Anthropic()

            tools = [
                {{
                    "name": "call_{func_name}",
                    "description": {json.dumps(api_desc)},
                    "input_schema": {{
                        "type": "object",
                        "properties": {{
                            "query": {{
                                "type": "string",
                                "description": "Search term or resource identifier."
                            }}
                        }},
                        "required": ["query"]
                    }}
                }}
            ]

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {{"role": "user", "content": "Find information using the {api_name} API."}}
                ],
                tools=tools,
            )
            print(response.content)
        """)
        st.code(claude_code, language="python")
        
    with tab_ollama:
        ollama_code = textwrap.dedent(f"""\
            import ollama

            tools = [
                {{
                    "type": "function",
                    "function": {{
                        "name": "call_{func_name}",
                        "description": {json.dumps(api_desc)},
                        "parameters": {{
                            "type": "object",
                            "properties": {{
                                "query": {{
                                    "type": "string",
                                    "description": "Search term or resource identifier."
                                }}
                            }},
                            "required": ["query"]
                        }}
                    }}
                }}
            ]

            response = ollama.chat(
                model="llama3.1",
                messages=[
                    {{"role": "user", "content": "Find information using the {api_name} API."}}
                ],
                tools=tools,
            )
            print(response['message'])
        """)
        st.code(ollama_code, language="python")



# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div style="text-align:center;padding:40px 0 20px 0;border-top:1px solid #21262d;margin-top:40px;">
        <p style="font-size:0.78rem;color:#484f58;">
            Built with ♥ using Streamlit&nbsp; ·&nbsp;
            Powered by the
            <a href="https://github.com/DP1110/-Premium-Multi-Agent-Boilerplate-Pack" target="_blank"
               style="color:#00ffcc;text-decoration:none;">Premium Multi-Agent Boilerplate Pack</a>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
