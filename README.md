# 🔱 Hermes — Multi-Agent SuperAgent

> **Greek Mythology**: The Messenger of the Gods — swift, resourceful, and boundary-crossing. Hermes carried messages between worlds; this engine carries tasks between specialized agents.

[![CI](https://github.com/MukundaKatta/hermes/actions/workflows/ci.yml/badge.svg)](https://github.com/MukundaKatta/hermes/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)

---

## What is Hermes?

Hermes is a **multi-agent orchestration engine** that decomposes complex tasks into subtasks, delegates them to specialized sub-agents, and aggregates the results — all with zero external dependencies.

### Features

- **Task Decomposition** — break high-level goals into dependency-aware step plans
- **Sub-Agent Delegation** — match tasks to agents by capability (research, code, create, review, test)
- **Code Sandbox** — execute Python code with stdout/stderr capture, timeout support, and persistent namespace
- **Tool Registry** — register, search, and invoke tools by name or keyword
- **CLI Interface** — `run`, `plan`, and `list-tools` commands out of the box
- **Zero Dependencies** — stdlib only in core; pytest and ruff for development

---

## Quick Start

```bash
git clone https://github.com/MukundaKatta/hermes.git
cd hermes
pip install -e ".[dev]"
```

### As a library

```python
from hermes import SuperAgent, SubAgent, AgentCapability, TaskPlan

# Create specialized agents
researcher = SubAgent(
    name="researcher",
    capabilities=[AgentCapability.RESEARCH],
    handler=lambda task: f"Researched: {task}",
)
coder = SubAgent(
    name="coder",
    capabilities=[AgentCapability.CODE],
    handler=lambda task: f"Coded: {task}",
)

# Build the super-agent and register sub-agents
sa = SuperAgent(name="Hermes")
sa.register_agent(researcher)
sa.register_agent(coder)

# Decompose a goal and execute
plan = sa.decompose("Research best practices and build a REST API")
results = sa.execute_plan(plan)
print(plan.summary())
```

### From the command line

```bash
# Preview an execution plan
python -m hermes plan "Research APIs and build a prototype"

# Execute a goal end-to-end
python -m hermes run "Create a data pipeline"

# List available tools
python -m hermes list-tools
```

---

## Architecture

```
                  ┌──────────────┐
                  │  SuperAgent  │
                  └──────┬───────┘
                         │ decomposes & delegates
            ┌────────────┼────────────┐
            ▼            ▼            ▼
      ┌──────────┐ ┌──────────┐ ┌──────────┐
      │ Research  │ │   Code   │ │  Create  │
      │  Agent   │ │  Agent   │ │  Agent   │
      └────┬─────┘ └────┬─────┘ └────┬─────┘
           │             │             │
           ▼             ▼             ▼
      ┌──────────┐ ┌──────────┐ ┌──────────┐
      │ ToolBelt │ │ Sandbox  │ │ ToolBelt │
      └──────────┘ └──────────┘ └──────────┘
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full details.

---

## Tech Stack

| Layer         | Technology     |
|---------------|----------------|
| Language      | Python 3.9+    |
| Build         | Hatch          |
| Testing       | pytest         |
| Linting       | ruff           |
| CI            | GitHub Actions |
| Dependencies  | None (stdlib)  |

---

## Development

```bash
make install   # pip install -e ".[dev]"
make test      # run test suite
make lint      # ruff check
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

---

## Inspired By

- **Hermes** (Greek Mythology) — messenger of the gods, patron of boundaries and transitions
- Multi-agent systems research — task decomposition, capability-based routing
- Unix philosophy — small, composable tools that do one thing well

---

## License

[MIT](LICENSE)
