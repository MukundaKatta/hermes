"""Command-line interface for Hermes.

Provides ``run``, ``plan``, and ``list-tools`` sub-commands.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from hermes.config import HermesConfig
from hermes.core import AgentCapability, SubAgent, SuperAgent
from hermes.sandbox import CodeSandbox
from hermes.tools import Tool, ToolBelt


def _default_handler(description: str) -> str:
    """Placeholder handler for built-in demo agents."""
    return f"[completed] {description}"


def _build_super_agent(config: HermesConfig) -> SuperAgent:
    """Create a SuperAgent pre-loaded with demo sub-agents."""
    sa = SuperAgent(name=config.agent_name)
    for cap in AgentCapability:
        sa.register_agent(
            SubAgent(
                name=f"{cap.value}-agent",
                capabilities=[cap],
                handler=_default_handler,
                max_retries=config.max_retries,
            )
        )
    return sa


def _build_tool_belt() -> ToolBelt:
    belt = ToolBelt()
    belt.register(Tool(
        name="echo",
        description="Echo the input back",
        handler=lambda text: text,
        tags=["utility"],
    ))
    belt.register(Tool(
        name="sandbox",
        description="Execute Python code in a sandbox",
        handler=lambda code: CodeSandbox().execute(code).stdout,
        tags=["code", "execute"],
    ))
    return belt


def cmd_run(args: argparse.Namespace, config: HermesConfig) -> None:
    """Execute a goal end-to-end."""
    sa = _build_super_agent(config)
    plan = sa.decompose(args.goal)
    results = sa.execute_plan(plan)

    print(plan.summary())
    for step in plan.steps:
        status = step.status.value.upper()
        agent = step.assigned_agent or "unassigned"
        print(f"  [{status}] ({agent}) {step.description}")
    if args.json:
        print(json.dumps(results, indent=2, default=str))


def cmd_plan(args: argparse.Namespace, config: HermesConfig) -> None:
    """Show the execution plan without running it."""
    sa = _build_super_agent(config)
    plan = sa.decompose(args.goal)
    print(f"Plan: {plan.goal}  ({len(plan.steps)} steps)")
    for idx, step in enumerate(plan.steps):
        deps = f" (depends on {step.depends_on})" if step.depends_on else ""
        print(f"  {idx}. [{step.required_capability.value}] {step.description}{deps}")


def cmd_list_tools(args: argparse.Namespace, config: HermesConfig) -> None:
    """List all registered tools."""
    belt = _build_tool_belt()
    for info in belt.list_tools():
        tags = ", ".join(info["tags"]) if info["tags"] else ""
        print(f"  {info['name']}: {info['description']}  [{tags}]")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hermes",
        description="Hermes — Multi-Agent SuperAgent",
    )
    parser.add_argument("--version", action="store_true", help="Show version")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Execute a goal")
    run_p.add_argument("goal", help="Goal to accomplish")
    run_p.add_argument("--json", action="store_true", help="Output JSON results")

    plan_p = sub.add_parser("plan", help="Show execution plan")
    plan_p.add_argument("goal", help="Goal to plan")

    sub.add_parser("list-tools", help="List available tools")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = HermesConfig()

    if args.version:
        from hermes import __version__
        print(f"hermes {__version__}")
        return 0

    dispatch = {
        "run": cmd_run,
        "plan": cmd_plan,
        "list-tools": cmd_list_tools,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    handler(args, config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
