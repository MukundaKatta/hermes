"""Core multi-agent orchestration engine.

Provides the SuperAgent class that decomposes complex tasks into subtasks,
delegates them to specialized sub-agents, and aggregates results.
"""
from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence


class TaskStatus(enum.Enum):
    """Lifecycle status of a task step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentCapability(enum.Enum):
    """Well-known capabilities a sub-agent can declare."""

    RESEARCH = "research"
    CODE = "code"
    CREATE = "create"
    REVIEW = "review"
    TEST = "test"
    GENERAL = "general"


@dataclass
class TaskStep:
    """A single atomic step inside a :class:`TaskPlan`.

    Attributes:
        description: Human-readable description of what the step does.
        required_capability: The capability needed to execute this step.
        depends_on: Indices of earlier steps that must complete first.
        status: Current lifecycle status.
        result: Arbitrary result payload once the step completes.
        step_id: Unique identifier (auto-generated).
        assigned_agent: Name of the agent assigned to this step.
    """

    description: str
    required_capability: AgentCapability = AgentCapability.GENERAL
    depends_on: List[int] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    step_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    assigned_agent: Optional[str] = None

    # ------------------------------------------------------------------
    @property
    def is_ready(self) -> bool:
        """Return *True* when all dependencies are satisfied."""
        return self.status == TaskStatus.PENDING

    def mark_running(self) -> None:
        self.status = TaskStatus.RUNNING

    def mark_completed(self, result: Any = None) -> None:
        self.status = TaskStatus.COMPLETED
        self.result = result

    def mark_failed(self, error: Any = None) -> None:
        self.status = TaskStatus.FAILED
        self.result = error

    def mark_skipped(self) -> None:
        self.status = TaskStatus.SKIPPED


@dataclass
class TaskPlan:
    """An ordered collection of :class:`TaskStep` objects that together
    accomplish a complex goal.

    Attributes:
        goal: The original high-level objective.
        steps: Ordered list of steps to execute.
        plan_id: Unique identifier.
        created_at: Timestamp of plan creation.
        metadata: Arbitrary key-value metadata.
    """

    goal: str
    steps: List[TaskStep] = field(default_factory=list)
    plan_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    def add_step(
        self,
        description: str,
        capability: AgentCapability = AgentCapability.GENERAL,
        depends_on: Optional[List[int]] = None,
    ) -> TaskStep:
        """Append a new step and return it."""
        step = TaskStep(
            description=description,
            required_capability=capability,
            depends_on=depends_on or [],
        )
        self.steps.append(step)
        return step

    def ready_steps(self) -> List[TaskStep]:
        """Return steps whose dependencies are all completed."""
        completed_indices: set[int] = set()
        for idx, step in enumerate(self.steps):
            if step.status == TaskStatus.COMPLETED:
                completed_indices.add(idx)

        ready: List[TaskStep] = []
        for step in self.steps:
            if step.status != TaskStatus.PENDING:
                continue
            if all(d in completed_indices for d in step.depends_on):
                ready.append(step)
        return ready

    @property
    def is_complete(self) -> bool:
        """All steps finished (completed, failed, or skipped)."""
        terminal = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED}
        return all(s.status in terminal for s in self.steps)

    @property
    def completed_steps(self) -> List[TaskStep]:
        return [s for s in self.steps if s.status == TaskStatus.COMPLETED]

    @property
    def failed_steps(self) -> List[TaskStep]:
        return [s for s in self.steps if s.status == TaskStatus.FAILED]

    @property
    def progress(self) -> float:
        """Fraction of steps in a terminal state (0.0 .. 1.0)."""
        if not self.steps:
            return 1.0
        terminal = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED}
        done = sum(1 for s in self.steps if s.status in terminal)
        return done / len(self.steps)

    def summary(self) -> str:
        """One-line human-readable progress summary."""
        total = len(self.steps)
        done = len(self.completed_steps)
        failed = len(self.failed_steps)
        return f"Plan '{self.goal}': {done}/{total} done, {failed} failed"


@dataclass
class SubAgent:
    """A lightweight specialist that can handle tasks matching its capabilities.

    Attributes:
        name: Human-readable agent name.
        capabilities: Set of capabilities this agent offers.
        handler: Callable that executes a task description and returns a result.
        agent_id: Unique identifier.
        max_retries: How many times to retry on failure.
    """

    name: str
    capabilities: List[AgentCapability]
    handler: Callable[[str], Any]
    agent_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    max_retries: int = 1

    def can_handle(self, capability: AgentCapability) -> bool:
        """Return *True* if this agent declares the given capability."""
        return capability in self.capabilities

    def execute(self, description: str) -> Any:
        """Run the handler, retrying up to *max_retries* times."""
        last_error: Optional[Exception] = None
        for _ in range(self.max_retries):
            try:
                return self.handler(description)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        raise RuntimeError(
            f"Agent '{self.name}' failed after {self.max_retries} attempt(s): {last_error}"
        ) from last_error


class SuperAgent:
    """Top-level orchestrator that decomposes goals, delegates to sub-agents,
    and aggregates results.

    Usage::

        sa = SuperAgent()
        sa.register_agent(researcher)
        sa.register_agent(coder)
        plan = sa.decompose("Build a REST API and write docs")
        results = sa.execute_plan(plan)
    """

    def __init__(self, name: str = "Hermes") -> None:
        self.name = name
        self._agents: Dict[str, SubAgent] = {}
        self._execution_log: List[Dict[str, Any]] = []

    # -- Agent management -----------------------------------------------

    def register_agent(self, agent: SubAgent) -> None:
        """Register a sub-agent."""
        self._agents[agent.agent_id] = agent

    def unregister_agent(self, agent_id: str) -> bool:
        """Remove a sub-agent by id. Returns True if removed."""
        return self._agents.pop(agent_id, None) is not None

    @property
    def agents(self) -> List[SubAgent]:
        return list(self._agents.values())

    def find_agent(self, capability: AgentCapability) -> Optional[SubAgent]:
        """Return the first agent that can handle *capability*, or *None*."""
        for agent in self._agents.values():
            if agent.can_handle(capability):
                return agent
        return None

    # -- Task decomposition ---------------------------------------------

    def decompose(
        self,
        goal: str,
        hints: Optional[Sequence[str]] = None,
    ) -> TaskPlan:
        """Break a high-level *goal* into a :class:`TaskPlan`.

        If *hints* are given they are used as step descriptions directly.
        Otherwise a simple keyword-based heuristic creates steps.
        """
        plan = TaskPlan(goal=goal)

        if hints:
            for idx, hint in enumerate(hints):
                cap = self._infer_capability(hint)
                depends = [idx - 1] if idx > 0 else []
                plan.add_step(hint, capability=cap, depends_on=depends)
            return plan

        # Simple keyword heuristic for demonstration
        keywords_map: Dict[str, AgentCapability] = {
            "research": AgentCapability.RESEARCH,
            "find": AgentCapability.RESEARCH,
            "search": AgentCapability.RESEARCH,
            "code": AgentCapability.CODE,
            "implement": AgentCapability.CODE,
            "build": AgentCapability.CODE,
            "write": AgentCapability.CREATE,
            "create": AgentCapability.CREATE,
            "generate": AgentCapability.CREATE,
            "review": AgentCapability.REVIEW,
            "test": AgentCapability.TEST,
        }

        lower_goal = goal.lower()
        capabilities_found: List[AgentCapability] = []
        for keyword, cap in keywords_map.items():
            if keyword in lower_goal and cap not in capabilities_found:
                capabilities_found.append(cap)

        if not capabilities_found:
            capabilities_found.append(AgentCapability.GENERAL)

        prev_idx: Optional[int] = None
        for cap in capabilities_found:
            depends = [prev_idx] if prev_idx is not None else []
            step = plan.add_step(
                f"{cap.value.capitalize()} phase for: {goal}",
                capability=cap,
                depends_on=depends,
            )
            prev_idx = len(plan.steps) - 1

        return plan

    # -- Execution ------------------------------------------------------

    def execute_plan(self, plan: TaskPlan) -> Dict[str, Any]:
        """Execute all steps in *plan*, respecting dependency order.

        Returns a dict mapping step_id -> result for every completed step.
        """
        max_iterations = len(plan.steps) * 2  # safety valve
        iteration = 0

        while not plan.is_complete and iteration < max_iterations:
            iteration += 1
            ready = plan.ready_steps()
            if not ready:
                # Remaining steps have unresolvable deps — skip them
                for step in plan.steps:
                    if step.status == TaskStatus.PENDING:
                        step.mark_skipped()
                break

            for step in ready:
                self._execute_step(step)

        results: Dict[str, Any] = {}
        for step in plan.steps:
            results[step.step_id] = step.result

        return results

    def _execute_step(self, step: TaskStep) -> None:
        """Assign a step to a matching agent and run it."""
        agent = self.find_agent(step.required_capability)
        if agent is None:
            step.mark_failed("No agent available for capability: "
                             f"{step.required_capability.value}")
            self._log("step_failed", step=step.step_id, reason="no_agent")
            return

        step.assigned_agent = agent.name
        step.mark_running()
        self._log("step_started", step=step.step_id, agent=agent.name)

        try:
            result = agent.execute(step.description)
            step.mark_completed(result)
            self._log("step_completed", step=step.step_id, result=result)
        except Exception as exc:  # noqa: BLE001
            step.mark_failed(str(exc))
            self._log("step_failed", step=step.step_id, error=str(exc))

    # -- Helpers --------------------------------------------------------

    @staticmethod
    def _infer_capability(text: str) -> AgentCapability:
        """Best-effort capability inference from free text."""
        lower = text.lower()
        if any(kw in lower for kw in ("research", "find", "search", "look up")):
            return AgentCapability.RESEARCH
        if any(kw in lower for kw in ("code", "implement", "build", "program")):
            return AgentCapability.CODE
        if any(kw in lower for kw in ("write", "create", "generate", "draft")):
            return AgentCapability.CREATE
        if any(kw in lower for kw in ("review", "audit", "check")):
            return AgentCapability.REVIEW
        if any(kw in lower for kw in ("test", "verify", "validate")):
            return AgentCapability.TEST
        return AgentCapability.GENERAL

    def _log(self, event: str, **kwargs: Any) -> None:
        entry = {"event": event, "time": time.time(), **kwargs}
        self._execution_log.append(entry)

    @property
    def execution_log(self) -> List[Dict[str, Any]]:
        return list(self._execution_log)
