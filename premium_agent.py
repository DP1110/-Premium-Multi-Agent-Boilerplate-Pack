"""
Toolify-API — Premium Multi-Agent Runner
==========================================
Demonstrates how to bind auto-generated public-API tool schemas to a
Google Gemini model and execute a fully autonomous function-calling loop.

Requirements:
    pip install google-genai requests

Usage:
    export GEMINI_API_KEY="your-key-here"
    python premium_agent.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import textwrap
from typing import Any, Callable
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

# Configure Windows consoles to use UTF-8 to prevent UnicodeEncodeErrors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

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

import requests
from google import genai
from google.genai import types



# ---------------------------------------------------------------------------
# Tool registry — maps function names to callable implementations
# ---------------------------------------------------------------------------

class ToolRegistry:
    """
    Maintains a mapping between Gemini tool-function names and their
    concrete Python implementations plus FunctionDeclaration metadata.
    """

    def __init__(self) -> None:
        self._functions: dict[str, Callable[..., Any]] = {}
        self._declarations: list[types.FunctionDeclaration] = []

    # -- registration -------------------------------------------------------

    def register(
        self,
        name: str,
        description: str,
        endpoint: str,
        auth_type: str = "",
    ) -> None:
        """
        Register a public API as a callable tool.

        Args:
            name: Sanitised function name (e.g. ``call_cat_facts``).
            description: One-line API description.
            endpoint: Base URL of the public API.
            auth_type: Auth scheme label (empty string means no auth).
        """
        # Build the concrete callable
        def _api_caller(query: str = "", api_key: str = "") -> dict:
            params: dict[str, str] = {}
            if query:
                params["q"] = query
            headers: dict[str, str] = {}
            if auth_type and api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            resp = requests.get(
                endpoint, params=params, headers=headers, timeout=30,
            )
            resp.raise_for_status()
            try:
                return resp.json()
            except requests.exceptions.JSONDecodeError:
                return {"raw_text": resp.text[:2000]}

        self._functions[name] = _api_caller

        # Build Gemini FunctionDeclaration
        properties: dict[str, types.Schema] = {
            "query": types.Schema(
                type="STRING",
                description="Search term or resource identifier.",
            ),
        }
        required = ["query"]

        if auth_type:
            properties["api_key"] = types.Schema(
                type="STRING",
                description="API authentication key or token.",
            )
            required.append("api_key")

        decl = types.FunctionDeclaration(
            name=name,
            description=description,
            parameters=types.Schema(
                type="OBJECT",
                properties=properties,
                required=required,
            ),
        )
        self._declarations.append(decl)

    # -- accessors ----------------------------------------------------------

    def get_tool(self) -> types.Tool:
        """Return a single ``types.Tool`` wrapping all registered declarations."""
        return types.Tool(function_declarations=self._declarations)

    def execute(self, name: str, args: dict[str, Any]) -> dict:
        """Look up and invoke a registered function by name."""
        fn = self._functions.get(name)
        if fn is None:
            return {"error": f"Unknown tool function: {name}"}
        try:
            return fn(**args)
        except Exception as exc:
            return {"error": str(exc)}

    @property
    def names(self) -> list[str]:
        return list(self._functions.keys())


# ---------------------------------------------------------------------------
# Gemini Agent
# ---------------------------------------------------------------------------

class ToolifyGeminiAgent:
    """
    Autonomous agent that:
      1. Accepts a natural-language prompt.
      2. Lets Gemini decide which public-API tools to call.
      3. Executes those tools via live HTTP requests.
      4. Feeds the results back as ``FunctionResponse`` parts.
      5. Continues until the model produces a final text answer.
    """

    MODEL = "gemini-2.5-flash"
    MAX_TURNS = 10  # safety limit

    def __init__(self, registry: ToolRegistry) -> None:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise EnvironmentError(
                "Set the GEMINI_API_KEY environment variable before running."
            )
        self.client = genai.Client(api_key=api_key)
        self.registry = registry

    # -- public interface ---------------------------------------------------

    def run(self, user_prompt: str) -> str:
        """
        Execute the full agent loop for *user_prompt* and return the
        model's final text response.
        """
        print(f"\n{'═' * 60}")
        print(f"  🧠  Toolify Agent — processing prompt")
        print(f"{'═' * 60}")
        print(f"  User: {user_prompt}\n")

        contents: list[types.Content] = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_prompt)],
            ),
        ]

        for turn in range(1, self.MAX_TURNS + 1):
            print(f"  ── Turn {turn} ──")

            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    tools=[self.registry.get_tool()],
                ),
            )

            # Check for function calls in the response
            function_calls = self._extract_function_calls(response)

            if not function_calls:
                # Model produced a final text answer
                final_text = response.text or "(no text response)"
                print(f"\n  ✅  Agent answer:\n{textwrap.indent(final_text, '      ')}\n")
                return final_text

            # Append the model's response (with function calls) to history
            contents.append(response.candidates[0].content)

            # Execute each function call and build FunctionResponse parts
            response_parts: list[types.Part] = []
            for fc in function_calls:
                fn_name = fc.name
                fn_args = dict(fc.args) if fc.args else {}
                print(f"    🔧  Calling {fn_name}({json.dumps(fn_args, default=str)})")

                result = self.registry.execute(fn_name, fn_args)

                # Truncate very large responses to stay within context limits
                result_str = json.dumps(result, default=str)
                if len(result_str) > 8000:
                    result = {"truncated": result_str[:8000], "note": "response truncated"}

                print(f"    📦  Result preview: {json.dumps(result, default=str)[:200]}…")

                response_parts.append(
                    types.Part.from_function_response(
                        name=fn_name,
                        response=result,
                    )
                )

            contents.append(
                types.Content(role="user", parts=response_parts),
            )

        return "(Agent reached maximum turn limit without a final answer.)"

    # -- internals ----------------------------------------------------------

    @staticmethod
    def _extract_function_calls(response) -> list:
        """Pull all FunctionCall objects from a GenerateContentResponse."""
        calls = []
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    calls.append(part.function_call)
        return calls


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def sanitize_name(raw: str) -> str:
    """Convert an API title into a valid Python identifier."""
    name = re.sub(r"[^a-zA-Z0-9]+", "_", raw.strip()).strip("_").lower()
    if name and name[0].isdigit():
        name = f"api_{name}"
    return name or "unnamed_api"


def build_registry_from_entries(entries: list[dict]) -> ToolRegistry:
    """
    Given a list of public-api entry dicts, register each as a tool.

    Args:
        entries: List of dicts with keys ``API``, ``Description``,
                 ``Link``, ``Auth``, ``HTTPS``, etc.
    """
    registry = ToolRegistry()
    for entry in entries:
        api_name = entry.get("API", "Unknown")
        func_name = f"call_{sanitize_name(api_name)}"
        description = entry.get("Description", f"Call the {api_name} API.")
        link = entry.get("Link", "")
        auth = entry.get("Auth", "")
        if link:
            registry.register(
                name=func_name,
                description=description,
                endpoint=link,
                auth_type=auth,
            )
    return registry


# ---------------------------------------------------------------------------
# Main — demo entry point
# ---------------------------------------------------------------------------

def fetch_and_parse_readme() -> list[dict]:
    """Download the public-apis README.md and parse the markdown tables."""
    url = "https://raw.githubusercontent.com/public-apis/public-apis/master/README.md"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    entries = []
    current_category = None
    link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    
    lines = resp.text.split("\n")
    for line in lines:
        line_str = line.strip()
        if line_str.startswith("### "):
            current_category = line_str[4:].strip()
            continue
            
        if current_category and "|" in line_str:
            if "API | Description" in line_str or "|:---" in line_str:
                continue
            
            parts = [p.strip() for p in line_str.split("|")]
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


def main() -> None:
    """
    Fetch a small subset of public APIs, register them as tools,
    and run a sample prompt through the autonomous agent loop.
    """
    print("⚡ Toolify-API Premium Agent")
    print("─" * 40)

    # Fetch the public-apis dataset
    print("📥  Fetching and parsing public API registry …")
    try:
        entries = fetch_and_parse_readme()
    except Exception as e:
        print(f"❌ Failed to fetch public-apis README.md: {e}")
        return


    # For the demo, register a curated subset to keep context manageable
    demo_categories = {"Animals", "Science", "Weather"}
    demo_entries = [
        e for e in entries
        if e.get("Category") in demo_categories
        and e.get("Auth", "") in ("", "No")
        and e.get("HTTPS", False)
    ][:8]

    print(f"📦  Registering {len(demo_entries)} tools …")
    registry = build_registry_from_entries(demo_entries)
    for name in registry.names:
        print(f"    • {name}")

    try:
        agent = ToolifyGeminiAgent(registry)
    except EnvironmentError as err:
        print(f"\n⚠️  {err}")
        print("Please set the environment variable and try again.")
        print("Example: set GEMINI_API_KEY=your-api-key")
        return

    # Run a sample prompt
    prompt = (
        "What are some interesting facts about cats? "
        "Use any available animal API to find out."
    )
    answer = agent.run(prompt)

    print("\n" + "═" * 60)
    print("  Final answer:")
    print(textwrap.indent(answer, "    "))
    print("═" * 60)


if __name__ == "__main__":
    main()
