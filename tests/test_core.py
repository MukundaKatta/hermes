"""Tests for hermes.core — SuperAgent, TaskPlan, SubAgent, TaskStep."""
from __future__ import annotations

import pytest

from hermes.core import (
    AgentCapability,
    SubAgent,
    SuperAgent,
    TaskPlan,
    TaskStatus,
    TaskStep,
)


# ── TaskStep ──────────────────────────────────────────────────────────


class TestTaskStep:
    def test_defaults(self) -> None:
        step = TaskStep(description="do something")
        assert step.status == TaskStatus.PENDING
        assert step.result is None
        assert step.depends_on == []
        assert step.is_ready

    def test_lifecycle_completed(self) -> None:
        step = TaskStep(description="work")
        step.mark_running()
        assert step.status == TaskStatus.RUNNING
        step.mark_completed("done")
        assert step.status == TaskStatus.COMPLETED
        assert step.result == "done"

    def test_lifecycle_failed(self) -> None:
        step = TaskStep(description="risky")
        step.mark_failed("boom")
        assert step.status == TaskStatus.FAILED
        assert step.result == "boom"

    def test_mark_skipped(self) -> None:
        step = TaskStep(description="optional")
        step.mark_skipped()
        assert step.status == TaskStatus.SKIPPED


# ── TaskPlan ──────────────────────────────────────────────────────────


class TestTaskPlan:
    def test_add_step(self) -> None:
        plan = TaskPlan(goal="test")
        step = plan.add_step("first", AgentCapability.CODE)
        assert len(plan.steps) == 1
        assert step.required_capability == AgentCapability.CODE

    def test_ready_steps_no_deps(self) -> None:
        plan = TaskPlan(goal="g")
        plan.add_step("a")
        plan.add_step("b")
        assert len(plan.ready_steps()) == 2

    def test_ready_steps_with_deps(self) -> None:
        plan = TaskPlan(goal="g")
        plan.add_step("a")
        plan.add_step("b", depends_on=[0])
        # Only step 0 is ready initially
        ready = plan.ready_steps()
        assert len(ready) == 1
        assert ready[0].description == "a"

    def test_is_complete(self) -> None:
        plan = TaskPlan(goal="g")
        plan.add_step("a")
        assert not plan.is_complete
        plan.steps[0].mark_completed()
        assert plan.is_complete

    def test_progress(self) -> None:
        plan = TaskPlan(goal="g")
        plan.add_step("a")
        plan.add_step("b")
        assert plan.progress == 0.0
        plan.steps[0].mark_completed()
        assert plan.progress == pytest.approx(0.5)

    def test_progress_empty_plan(self) -> None:
        plan = TaskPlan(goal="empty")
        assert plan.progress == 1.0

    def test_summary(self) -> None:
        plan = TaskPlan(goal="demo")
        plan.add_step("s1")
        plan.steps[0].mark_completed()
        assert "1/1 done" in plan.summary()


# ── SubAgent ──────────────────────────────────────────────────────────


class TestSubAgent:
    def test_can_handle(self) -> None:
        agent = SubAgent(
            name="coder",
            capabilities=[AgentCapability.CODE],
            handler=lambda d: d,
        )
        assert agent.can_handle(AgentCapability.CODE)
        assert not agent.can_handle(AgentCapability.RESEARCH)

    def test_execute_success(self) -> None:
        agent = SubAgent(
            name="echo",
            capabilities=[AgentCapability.GENERAL],
            handler=lambda d: f"echo: {d}",
        )
        assert agent.execute("hi") == "echo: hi"

    def test_execute_retry_failure(self) -> None:
        call_count = 0

        def flaky(desc: str) -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError("nope")

        agent = SubAgent(
            name="flaky",
            capabilities=[AgentCapability.GENERAL],
            handler=flaky,
            max_retries=3,
        )
        with pytest.raises(RuntimeError, match="3 attempt"):
            agent.execute("anything")
        assert call_count == 3


# ── SuperAgent ────────────────────────────────────────────────────────


class TestSuperAgent:
    def _make_agent(
        self, cap: AgentCapability, name: str = "a"
    ) -> SubAgent:
        return SubAgent(
            name=name,
            capabilities=[cap],
            handler=lambda d: f"done: {d}",
        )

    def test_register_and_find(self) -> None:
        sa = SuperAgent()
        agent = self._make_agent(AgentCapability.CODE, "coder")
        sa.register_agent(agent)
        assert sa.find_agent(AgentCapability.CODE) is agent
        assert sa.find_agent(AgentCapability.RESEARCH) is None

    def test_unregister(self) -> None:
        sa = SuperAgent()
        agent = self._make_agent(AgentCapability.CODE, "coder")
        sa.register_agent(agent)
        assert sa.unregister_agent(agent.agent_id)
        assert not sa.unregister_agent("nonexistent")
        assert sa.agents == []

    def test_decompose_with_hints(self) -> None:
        sa = SuperAgent()
        plan = sa.decompose("build app", hints=["research APIs", "code it"])
        assert len(plan.steps) == 2
        assert plan.steps[0].required_capability == AgentCapability.RESEARCH
        assert plan.steps[1].required_capability == AgentCapability.CODE

    def test_decompose_keyword_heuristic(self) -> None:
        sa = SuperAgent()
        plan = sa.decompose("research and build a REST API")
        caps = [s.required_capability for s in plan.steps]
        assert AgentCapability.RESEARCH in caps
        assert AgentCapability.CODE in caps

    def test_decompose_fallback_general(self) -> None:
        sa = SuperAgent()
        plan = sa.decompose("do something vague")
        assert len(plan.steps) == 1
        assert plan.steps[0].required_capability == AgentCapability.GENERAL

    def test_execute_plan_simple(self) -> None:
        sa = SuperAgent()
        sa.register_agent(self._make_agent(AgentCapability.GENERAL, "worker"))
        plan = TaskPlan(goal="simple")
        plan.add_step("do it", AgentCapability.GENERAL)
        results = sa.execute_plan(plan)
        assert plan.is_complete
        assert any("done:" in str(v) for v in results.values())

    def test_execute_plan_no_agent_fails_step(self) -> None:
        sa = SuperAgent()
        plan = TaskPlan(goal="orphan")
        plan.add_step("code stuff", AgentCapability.CODE)
        sa.execute_plan(plan)
        assert plan.steps[0].status == TaskStatus.FAILED

    def test_execute_plan_dependency_chain(self) -> None:
        sa = SuperAgent()
        sa.register_agent(self._make_agent(AgentCapability.RESEARCH, "r"))
        sa.register_agent(self._make_agent(AgentCapability.CODE, "c"))

        plan = TaskPlan(goal="chained")
        plan.add_step("research", AgentCapability.RESEARCH)
        plan.add_step("code", AgentCapability.CODE, depends_on=[0])

        sa.execute_plan(plan)
        assert plan.is_complete
        assert plan.steps[0].status == TaskStatus.COMPLETED
        assert plan.steps[1].status == TaskStatus.COMPLETED

    def test_execution_log(self) -> None:
        sa = SuperAgent()
        sa.register_agent(self._make_agent(AgentCapability.GENERAL, "w"))
        plan = TaskPlan(goal="log test")
        plan.add_step("x", AgentCapability.GENERAL)
        sa.execute_plan(plan)
        assert len(sa.execution_log) >= 2  # started + completed
