import pathlib
import re
import sys
import time
from sys import implementation

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from agent.tools import PROJECT_ROOT, write_file, read_file

load_dotenv()

from langchain_groq import ChatGroq
from agent.prompts import *
from agent.states import *
from langgraph.constants import END
from langgraph.graph import StateGraph
from langchain_core.globals import set_verbose, set_debug

set_debug(False)
set_verbose(False)

llm = ChatGroq(model="openai/gpt-oss-120b")

from pydantic import BaseModel

user_prompt = "create a simple calculator web application"


def compact_text(text: str, max_chars: int = 3000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n...[truncated]..."


def strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return text

    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip() + "\n"
    return text


def strip_accidental_tool_call(text: str) -> str:
    stripped = text.strip()
    match = re.fullmatch(
        r"write_file\(\s*['\"][^'\"]+['\"]\s*,\s*(?P<quote>'''|\"\"\")(?P<body>.*)(?P=quote)\s*\)\s*",
        stripped,
        flags=re.DOTALL,
    )
    if match:
        return match.group("body").strip() + "\n"
    return text


def normalize_generated_content(filepath: str, content: str) -> str:
    content = strip_accidental_tool_call(strip_markdown_fence(content))
    suffix = pathlib.Path(filepath).suffix.lower()
    if suffix == ".html":
        content = content.replace('src="script.js"', 'src="app.js"')
        content = content.replace("src='script.js'", "src='app.js'")
        content = content.replace('href="style.css"', 'href="styles.css"')
        content = content.replace("href='style.css'", "href='styles.css'")
    if suffix == ".js":
        content = re.sub(r"\n?\s*export\s*\{.*?\};?\s*$", "", content, flags=re.DOTALL)
    return content


def read_project_file(path: str) -> str:
    project_path = PROJECT_ROOT / path
    if not project_path.exists() or not project_path.is_file():
        return ""
    return compact_text(project_path.read_text(encoding="utf-8", errors="replace"), 2500)


def generated_context_for(filepath: str) -> str:
    related = []
    for path in ("index.html", "styles.css", "app.js"):
        if path == filepath:
            continue
        content = read_project_file(path)
        if content:
            related.append(f"--- {path} ---\n{content}")
    return "\n\n".join(related) if related else "No related files have been generated yet."


def repair_generated_project(state: dict) -> dict:
    index_path = PROJECT_ROOT / "index.html"
    if not index_path.exists():
        return state

    html = index_path.read_text(encoding="utf-8", errors="replace")
    html = normalize_generated_content("index.html", html)

    if "styles.css" not in html and "</head>" in html:
        html = html.replace("</head>", '    <link rel="stylesheet" href="styles.css">\n</head>', 1)
    if "app.js" not in html and "</body>" in html:
        html = html.replace("</body>", '    <script src="app.js" defer></script>\n</body>', 1)

    index_path.write_text(html, encoding="utf-8")

    for path in PROJECT_ROOT.glob("*"):
        if path.is_file() and path.suffix.lower() in {".html", ".css", ".js", ".md"}:
            content = path.read_text(encoding="utf-8", errors="replace")
            normalized = normalize_generated_content(path.name, content)
            if normalized != content:
                path.write_text(normalized, encoding="utf-8")

    return state


def invoke_with_rate_limit_retry(runnable, payload, config=None):
    try:
        if config is None:
            return runnable.invoke(payload)
        return runnable.invoke(payload, config)
    except Exception as exc:
        message = str(exc).lower()
        if "rate_limit_exceeded" not in message and "tokens per minute" not in message:
            raise
        print("Groq token-per-minute limit reached. Waiting 65 seconds, then retrying once...")
        time.sleep(65)
        if config is None:
            return runnable.invoke(payload)
        return runnable.invoke(payload, config)

def planner_agent(state:dict) -> dict:
    users_prompt = state["user_prompt"]
    resp = invoke_with_rate_limit_retry(llm.with_structured_output(Plan), planner_prompt(users_prompt))
    if resp is None:
        raise ValueError("Planner did not return a valid response.")
    return {"plan":resp}


def architect_agent(state:dict) -> dict:
    plan: Plan = state["plan"]
    browser_defaults = {
        "index.html": "Main HTML entry point with semantic markup, linked styles.css, and deferred app.js.",
        "styles.css": "Responsive polished visual design for the app using selectors from index.html.",
        "app.js": "Complete browser behavior using selectors from index.html, local state, and localStorage when useful.",
        "README.md": "Short usage notes explaining how to open index.html and what the app does.",
    }
    file_purposes = {file.path: file.purpose for file in plan.files}
    if "html" in plan.techstack.lower() or "javascript" in plan.techstack.lower() or "web" in plan.techstack.lower():
        file_purposes = {**browser_defaults, **file_purposes}

    priority = {"index.html": 0, "styles.css": 1, "app.js": 2, "README.md": 3}
    ordered_files = sorted(file_purposes.items(), key=lambda item: (priority.get(item[0], 50), item[0]))
    steps = [
        ImplementationTask(
            filepath=path,
            task_description=f"Create the complete {path} file. Purpose: {purpose}",
        )
        for path, purpose in ordered_files
    ]
    task_plan = TaskPlan(implementation_steps=steps)
    task_plan.plan = plan
    return {"task_plan": task_plan}

def coder_agent(state:dict) -> dict:
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"],current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    if coder_state.current_step_idx >= len(steps):
        return {"coder_state":coder_state,"status":"DONE"}

    current_task = steps[coder_state.current_step_idx]
    existing_content = read_file.invoke({"path": current_task.filepath})
    existing_content = compact_text(existing_content)
    plan = getattr(coder_state.task_plan, "plan", None)
    file_contract = "\n".join(f"- {step.filepath}: {step.task_description}" for step in steps)
    related_files = generated_context_for(current_task.filepath)

    system_prompt = coder_system_prompt()
    coder_prompt = (
        f"Original project plan:\n{plan}\n\n"
        f"Required file contract:\n{file_contract}\n\n"
        f"Already generated related files:\n{related_files}\n\n"
        f"Task: {current_task.task_description}\n"
        f"File: {current_task.filepath}\n"
        f"Existing content:\n{existing_content}\n"
        "Return only the complete final file content. Do not wrap it in markdown."
    )

    response = invoke_with_rate_limit_retry(
        llm,
        [("system", system_prompt), ("user", coder_prompt)]
    )
    content = normalize_generated_content(current_task.filepath, response.content)
    write_result = write_file.invoke({"path": current_task.filepath, "content": content})
    if isinstance(write_result, str) and write_result.startswith("ERROR:"):
        raise ValueError(write_result)
    coder_state.current_step_idx += 1
    return {"coder_state":coder_state}

graph = StateGraph(dict)
graph.add_node("planner",planner_agent)
graph.add_node("architect",architect_agent)
graph.add_node("coder",coder_agent)
graph.add_node("repair", repair_generated_project)
graph.add_edge("planner","architect")
graph.add_edge("architect","coder")
graph.add_conditional_edges(
    "coder",
    lambda s: "repair" if s.get("status") == "DONE" else "coder",
    {"repair": "repair", "coder": "coder"}
)
graph.add_edge("repair", END)
graph.set_entry_point("planner")

agent = graph.compile()

if __name__ == "__main__":
    result = invoke_with_rate_limit_retry(
        agent,
        {"user_prompt": "Build a colourful modern todo app in html css and js"},
        {"recursion_limit": 100}
    )
    print("Final State:", result)
