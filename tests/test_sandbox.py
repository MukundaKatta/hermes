"""Tests for hermes.sandbox — CodeSandbox and ExecutionResult."""
from __future__ import annotations

from hermes.sandbox import CodeSandbox, ExecutionResult


class TestExecutionResult:
    def test_output_combined(self) -> None:
        r = ExecutionResult(stdout="hello", stderr="warn")
        assert "hello" in r.output
        assert "warn" in r.output

    def test_output_empty(self) -> None:
        r = ExecutionResult()
        assert r.output == ""


class TestCodeSandbox:
    def test_simple_print(self) -> None:
        sb = CodeSandbox()
        result = sb.execute("print('hello world')")
        assert result.success
        assert result.stdout.strip() == "hello world"

    def test_variable_persistence(self) -> None:
        sb = CodeSandbox()
        sb.execute("x = 42")
        result = sb.execute("print(x)")
        assert result.success
        assert "42" in result.stdout

    def test_syntax_error(self) -> None:
        sb = CodeSandbox()
        result = sb.execute("def bad(")
        assert not result.success
        assert "SyntaxError" in result.stderr

    def test_runtime_error(self) -> None:
        sb = CodeSandbox()
        result = sb.execute("1 / 0")
        assert not result.success
        assert "ZeroDivisionError" in result.stderr

    def test_history(self) -> None:
        sb = CodeSandbox()
        sb.execute("a = 1")
        sb.execute("b = 2")
        assert len(sb.history) == 2
        assert sb.execution_count == 2

    def test_last_result(self) -> None:
        sb = CodeSandbox()
        assert sb.last_result is None
        sb.execute("x = 1")
        assert sb.last_result is not None
        assert sb.last_result.success

    def test_reset(self) -> None:
        sb = CodeSandbox()
        sb.execute("x = 1")
        sb.reset()
        assert sb.history == []
        assert sb.execution_count == 0
        result = sb.execute("print(x)")
        assert not result.success  # x no longer defined

    def test_namespace_keys(self) -> None:
        sb = CodeSandbox()
        sb.execute("alpha = 1\nbeta = 2")
        keys = sb.namespace_keys
        assert "alpha" in keys
        assert "beta" in keys

    def test_exec_id_increments(self) -> None:
        sb = CodeSandbox()
        r1 = sb.execute("pass")
        r2 = sb.execute("pass")
        assert r1.exec_id == 1
        assert r2.exec_id == 2
