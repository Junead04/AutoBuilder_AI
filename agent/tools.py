import pathlib
import subprocess
from typing import Tuple

from langchain_core.tools import tool

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent / "generated_project"
PROJECT_ROOT = PROJECT_ROOT.resolve()


def safe_path_for_project(path: str) -> pathlib.Path:
    raw_path = pathlib.Path(path or ".")
    if not raw_path.is_absolute() and raw_path.parts and raw_path.parts[0] == PROJECT_ROOT.name:
        raw_path = pathlib.Path(*raw_path.parts[1:]) if len(raw_path.parts) > 1 else pathlib.Path(".")
    p = raw_path.resolve() if raw_path.is_absolute() else (PROJECT_ROOT / raw_path).resolve()
    if not p.is_relative_to(PROJECT_ROOT):
        raise ValueError(f"Attempt to access outside project root: {path}")
    return p


@tool
def write_file(path: str, content: str) -> str:
    """Writes content to a file at the specified path within the project root."""
    try:
        p = safe_path_for_project(path)
    except ValueError as exc:
        return f"ERROR: {exc}"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return f"WROTE:{p}"


@tool
def read_file(path: str) -> str:
    """Reads content from a file at the specified path within the project root."""
    try:
        p = safe_path_for_project(path)
    except ValueError as exc:
        return f"ERROR: {exc}"
    if not p.exists():
        return ""
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


@tool
def get_current_directory() -> str:
    """Returns the current working directory."""
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    return str(PROJECT_ROOT)


@tool
def list_files(directory: str = ".") -> str:
    """Lists all files in the specified directory within the project root."""
    try:
        p = safe_path_for_project(directory)
    except ValueError as exc:
        return f"ERROR: {exc}"
    if p == PROJECT_ROOT and not p.exists():
        return "No files found."
    if not p.is_dir():
        return f"ERROR: {p} is not a directory"
    files = [str(f.relative_to(PROJECT_ROOT)) for f in p.glob("**/*") if f.is_file()]
    return "\n".join(files) if files else "No files found."

@tool
def run_cmd(cmd: str, cwd: str = None, timeout: int = 30) -> Tuple[int, str, str]:
    """Runs a shell command in the specified directory and returns the result."""
    try:
        cwd_dir = safe_path_for_project(cwd) if cwd else PROJECT_ROOT
    except ValueError as exc:
        return 1, "", str(exc)
    cwd_dir.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(cmd, shell=True, cwd=str(cwd_dir), capture_output=True, text=True, timeout=timeout)
    return res.returncode, res.stdout, res.stderr


def init_project_root():
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    return str(PROJECT_ROOT)
