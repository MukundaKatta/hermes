# Architecture

## Overview

Hermes is a multi-agent orchestration engine built around four core modules:

```
                  ┌──────────────┐
                  │  SuperAgent  │
                  │  (core.py)   │
                  └──────┬───────┘
                         │ decomposes & delegates
            ┌────────────┼────────────┐
            ▼            ▼            ▼
      ┌──────────┐ ┌──────────┐ ┌──────────┐
      │ SubAgent │ │ SubAgent │ │ SubAgent │
      │ Research │ │   Code   │ │  Create  │
      └────┬─────┘ └────┬─────┘ └────┬─────┘
           │             │             │
           ▼             ▼             ▼
      ┌──────────┐ ┌──────────┐ ┌──────────┐
      │ ToolBelt │ │ Sandbox  │ │ ToolBelt │
      └──────────┘ └──────────┘ └──────────┘
```

## Modules

### core.py — Orchestration

- **SuperAgent**: Top-level coordinator. Decomposes goals into a `TaskPlan`, assigns steps to `SubAgent` instances, and aggregates results.
- **TaskPlan**: Ordered list of `TaskStep` objects with dependency tracking.
- **SubAgent**: Specialist worker with declared capabilities and a handler function.

### sandbox.py — Code Execution

- **CodeSandbox**: Executes Python code strings in an isolated namespace with stdout/stderr capture, timeout support, and execution history.

### tools.py — Tool Registry

- **ToolBelt**: Register, search, and invoke tools by name or keyword.
- **Tool**: Dataclass wrapping a callable with metadata for discoverability.

### config.py — Configuration

- **HermesConfig**: Dataclass with environment variable overrides (`HERMES_*` prefix).

### cli.py — Command Line

Three sub-commands: `run` (execute a goal), `plan` (preview without executing), `list-tools` (show registered tools).

## Data Flow

1. User provides a goal string via CLI or API.
2. `SuperAgent.decompose()` breaks the goal into a `TaskPlan`.
3. `SuperAgent.execute_plan()` iterates ready steps, finds matching agents, and delegates.
4. Each `SubAgent.execute()` runs its handler (which may use `CodeSandbox` or `ToolBelt`).
5. Results are aggregated and returned.

## Design Principles

- **Zero external dependencies** in core — stdlib only.
- **Type-hinted** throughout for IDE and mypy support.
- **Python 3.9+** compatible via `from __future__ import annotations`.
