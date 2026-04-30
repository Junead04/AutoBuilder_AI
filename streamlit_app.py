import os
import pathlib
import shutil
import traceback

import streamlit as st
import streamlit.components.v1 as components

from agent.graph import agent
from agent.tools import PROJECT_ROOT


ROOT = pathlib.Path(PROJECT_ROOT)
INDEX_FILE = ROOT / "index.html"


st.set_page_config(
    page_title="App Builder",
    page_icon="AB",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    :root {
        --surface: #ffffff;
        --panel: #f7f9fc;
        --line: #d9e2ef;
        --text-muted: #53657d;
        --brand: #0f766e;
        --brand-dark: #115e59;
        --accent: #f59e0b;
    }

    .stApp {
        background: #eef3f8;
        color: #122033;
    }

    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
        max-width: 1440px;
    }

    [data-testid="stSidebar"] {
        background: #172033;
        color: #f8fafc;
    }

    [data-testid="stSidebar"] * {
        color: #f8fafc;
    }

    .app-shell {
        border: 1px solid var(--line);
        background: var(--surface);
        border-radius: 8px;
        padding: 18px 20px;
        margin-bottom: 16px;
    }

    .header-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 18px;
        border-bottom: 1px solid var(--line);
        padding-bottom: 14px;
        margin-bottom: 16px;
    }

    .brand-title {
        font-size: 1.45rem;
        font-weight: 750;
        margin: 0;
        letter-spacing: 0;
    }

    .brand-subtitle {
        color: var(--text-muted);
        margin: 4px 0 0;
        font-size: 0.92rem;
    }

    .status-pill {
        border: 1px solid #b8c7d9;
        background: #f8fafc;
        color: #334155;
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 0.82rem;
        white-space: nowrap;
    }

    .metric-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
    }

    .metric-box {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--panel);
        padding: 12px;
    }

    .metric-label {
        color: var(--text-muted);
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .metric-value {
        color: #0f172a;
        font-size: 1.05rem;
        font-weight: 720;
        margin-top: 4px;
    }

    .file-row {
        border: 1px solid var(--line);
        background: #ffffff;
        border-radius: 6px;
        padding: 9px 10px;
        margin-bottom: 7px;
        font-size: 0.88rem;
    }

    div.stButton > button {
        border-radius: 6px;
        border: 1px solid #0f766e;
        background: #0f766e;
        color: #ffffff;
        font-weight: 650;
    }

    div.stButton > button:hover {
        border-color: #115e59;
        background: #115e59;
        color: #ffffff;
    }

    div[data-testid="stTextArea"] textarea {
        border-radius: 8px;
        border: 1px solid #b8c7d9;
        font-size: 0.98rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def list_generated_files() -> list[pathlib.Path]:
    if not ROOT.exists():
        return []
    return sorted(path for path in ROOT.rglob("*") if path.is_file())


def relative_name(path: pathlib.Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def clean_generated_project() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    for item in ROOT.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def file_uri(path: pathlib.Path) -> str:
    return path.resolve().as_uri()


def generate_project(prompt: str, recursion_limit: int) -> None:
    agent.invoke({"user_prompt": prompt}, {"recursion_limit": recursion_limit})


def read_text(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def html_preview_source() -> str:
    html = read_text(INDEX_FILE)
    base_tag = f'<base href="{ROOT.resolve().as_uri()}/">'
    if "<head>" in html:
        return html.replace("<head>", f"<head>\n    {base_tag}", 1)
    return base_tag + html


with st.sidebar:
    st.markdown("## App Builder")
    st.caption("Generate small web apps from prompts.")
    recursion_limit = st.slider("Recursion limit", 20, 160, 100, 10)
    auto_clean = st.toggle("Clean output before generate", value=True)
    st.divider()
    st.markdown("**Output folder**")
    st.code(str(ROOT), language="text")
    st.markdown("**Run command**")
    st.code("streamlit run streamlit_app.py", language="powershell")


st.markdown(
    """
    <div class="app-shell">
      <div class="header-row">
        <div>
          <p class="brand-title">Enterprise App Builder</p>
          <p class="brand-subtitle">Describe the app you want, generate the code folder, preview it, and open it directly.</p>
        </div>
        <div class="status-pill">Local generator</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

prompt = st.text_area(
    "Application prompt",
    value="Build a colourful modern todo app in HTML, CSS, and JavaScript with filters and localStorage.",
    height=116,
    placeholder="Example: Build a CRM dashboard with cards, charts, and a responsive sidebar.",
)

actions = st.columns([1.2, 1, 4])
generate_clicked = actions[0].button("Generate app", type="primary", use_container_width=True)
open_clicked = actions[1].button("Open web app", use_container_width=True, disabled=not INDEX_FILE.exists())

if open_clicked and INDEX_FILE.exists():
    os.startfile(str(INDEX_FILE))
    st.toast("Opened generated index.html in your browser.")

if generate_clicked:
    if not prompt.strip():
        st.error("Enter a prompt before generating.")
    else:
        try:
            with st.status("Generating project...", expanded=True) as status:
                st.write("Preparing output folder.")
                if auto_clean:
                    clean_generated_project()
                st.write("Calling the planner and code generator.")
                generate_project(prompt.strip(), recursion_limit)
                st.write("Refreshing generated files.")
                status.update(label="Generation complete", state="complete")
            st.success("Generated the project.")
        except Exception as exc:
            st.error(f"Generation failed: {exc}")
            with st.expander("Error details"):
                st.code(traceback.format_exc(), language="text")


files = list_generated_files()
file_count = len(files)
total_size = sum(path.stat().st_size for path in files) if files else 0
entrypoint = "Ready" if INDEX_FILE.exists() else "Missing index.html"

st.markdown(
    f"""
    <div class="metric-strip">
      <div class="metric-box">
        <div class="metric-label">Files</div>
        <div class="metric-value">{file_count}</div>
      </div>
      <div class="metric-box">
        <div class="metric-label">Output size</div>
        <div class="metric-value">{total_size / 1024:.1f} KB</div>
      </div>
      <div class="metric-box">
        <div class="metric-label">Web app</div>
        <div class="metric-value">{entrypoint}</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([0.36, 0.64], gap="large")

with left:
    st.subheader("Code Folder")
    if not files:
        st.info("No generated files yet.")
    else:
        for path in files:
            st.markdown(
                f'<div class="file-row">{relative_name(path)} · {path.stat().st_size} bytes</div>',
                unsafe_allow_html=True,
            )

    if INDEX_FILE.exists():
        st.link_button("Open index.html link", file_uri(INDEX_FILE), use_container_width=True)

    selected_name = None
    if files:
        selected_name = st.selectbox("Preview file", [relative_name(path) for path in files])

with right:
    tab_preview, tab_code = st.tabs(["Web Preview", "Code Preview"])

    with tab_preview:
        if INDEX_FILE.exists():
            html = html_preview_source()
            components.html(html, height=640, scrolling=True)
            st.caption("Preview uses the generated HTML. Use Open web app for the full browser version with linked CSS and JS.")
        else:
            st.info("Generate an app with an index.html file to preview it here.")

    with tab_code:
        if selected_name:
            selected_path = ROOT / selected_name
            suffix = selected_path.suffix.lower().lstrip(".") or "text"
            language = {"js": "javascript", "css": "css", "html": "html", "md": "markdown"}.get(suffix, "text")
            st.code(read_text(selected_path), language=language)
        else:
            st.info("Select a generated file to inspect its code.")
