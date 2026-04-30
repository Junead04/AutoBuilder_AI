def planner_prompt(user_prompt:str)->str:
    PLANNER_PROMPT = f"""
    You are the PLANNER agent. Convert the user prompt into a concise engineering project plan.
    For browser apps, use exactly these files unless the user explicitly asks otherwise:
    - index.html
    - styles.css
    - app.js
    - README.md

    The generated app must run by opening index.html directly in a browser.

    User request:{user_prompt}
    """
    return PLANNER_PROMPT

def architect_prompt(plan: str) -> str:
    ARCHITECT_PROMPT = f"""
You are the ARCHITECT agent. Given this project plan, break it down into concise file-level tasks.

RULES:
- Create exactly one implementation task per file.
- Keep each task description under 80 words.
- Include only the behavior needed for that file.
- Order tasks so that dependencies are implemented first.

Project Plan:
{plan}
    """
    return ARCHITECT_PROMPT

def coder_system_prompt() -> str:
    CODER_SYSTEM_PROMPT = """
You are the CODER agent.
Implement only the requested file.
Return raw file content only. Do not call tools. Do not include write_file(...).
Do not wrap output in markdown fences.

For browser apps:
- index.html must link to styles.css and load app.js with <script src="app.js" defer></script>.
- Do not use script.js, main.js, style.css, or inline JavaScript.
- Use stable IDs/classes and keep app.js selectors exactly aligned with index.html.
- Implement complete working interactions, not placeholders.
- styles.css should make the app polished, responsive, and readable on mobile and desktop.
    """
    return CODER_SYSTEM_PROMPT
