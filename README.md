# 🚀 AutoBuilder AI

AutoBuilder AI is an AI-powered application builder that transforms natural language prompts into fully functional software projects using a multi-agent system.

It simulates a real-world development workflow by coordinating multiple intelligent agents that plan, design, and generate code — file by file — just like a professional engineering team.

---

## 🧠 How It Works

AutoBuilder AI uses an agentic architecture powered by LangGraph:

### 🔹 Planner Agent
- Understands the user's prompt
- Generates a structured high-level plan

### 🔹 Architect Agent
- Converts the plan into detailed engineering tasks
- Defines file structure and responsibilities

### 🔹 Coder Agent
- Executes tasks step-by-step
- Writes and updates files directly
- Uses tools like file system access (read/write/list)

---

## 🏗️ Architecture

```
User Prompt
     ↓
Planner Agent → Generates Plan
     ↓
Architect Agent → Creates Task Breakdown
     ↓
Coder Agent → Generates Code + Files
     ↓
Generated Project Folder
```

---

## ⚙️ Tech Stack

- **LangGraph** – Multi-agent workflow orchestration
- **LangChain** – LLM integration & tools
- **Groq LLM** – Fast inference for generation
- **Python** – Core backend logic
- **Streamlit** – UI (optional interface)

---

## 🚀 Getting Started

### 🔧 Prerequisites

- Python 3.10+
- `uv` (recommended package manager)
- Groq API key

### ⚙️ Installation

```bash
# Clone the repository
git clone https://github.com/Junead04/AutoBuilder_AI.git
cd AutoBuilder_AI

# Create virtual environment
uv venv
.venv\Scripts\activate   # Windows

# Install dependencies
uv pip install -r pyproject.toml
```

### 🔑 Environment Setup

Create a `.env` file:

```env
GROQ_API_KEY=your_api_key_here
```

### ▶️ Run the Application

```bash
python main.py
```

Or if using Streamlit UI:

```bash
streamlit run streamlit_app.py
```

---

## 🧪 Example Prompts

Try these inputs:

```
Create a to-do list application using HTML, CSS, and JavaScript.
Create a simple calculator web application.
Build a colorful modern notes app with local storage.
Create a simple blog API using FastAPI and SQLite.
```

---

## 📁 Output

The system generates a complete project inside:

```
generated_project/
```

You can run web apps by opening:

```
index.html
```

Or using:

```bash
python -m http.server 5500
```

---

## 💡 Key Features

- 🧠 Multi-agent AI system
- 🏗️ End-to-end project generation
- 📂 Real file creation (not just text output)
- 🔁 Iterative task execution
- ⚡ Fast LLM responses (Groq)

---

## 🚀 Future Improvements

- Code execution & debugging agent
- Frontend UI enhancements
- Memory & context awareness
- Deployment automation

---

## 👨‍💻 Author

**Junead** — Aspiring AI Engineer | Building real-world AI systems

---

## ⭐ Support

If you like this project:

- ⭐ Star the repo
- 🍴 Fork it
- 📢 Share it

---

## 📜 License

This project is open-source and available for learning and development purposes.
