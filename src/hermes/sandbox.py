"""Safe code execution sandbox.

Provides a :class:`CodeSandbox` that captures stdout / stderr, enforces
timeouts, and keeps a memory of past executions.
"""
from __future__ import annotations

import io
import contextlib
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionResult:
    """Captures the outcome of a single sandbox execution.

    Attributes:
        stdout: Captured standard output.
        stderr: Captured standard error / traceback.
        return_value: The value of the last expression (when applicable).
        success: Whether the execution completed without raising.
        elapsed: Wall-clock seconds the execution took.
        exec_id: Sequential execution counter scoped to the sandbox.
    """

    stdout: str = ""
    stderr: str = ""
    return_value: Any = None
    success: bool = True
    elapsed: float = 0.0
    exec_id: int = 0

    @property
    def output(self) -> str:
        """Combined stdout + stderr for quick inspection."""
        parts: list[str] = []
        if self.stdout:
            parts.append(self.stdout)
        if self.stderr:
            parts.append(self.stderr)
        return "\n".join(parts)


class CodeSandbox:
    """Execute Python code strings in an isolated namespace.

    Features:
    * Captures stdout and stderr separately.
    * Enforces a wall-clock *timeout* (simple pre-check, not preemptive).
    * Maintains a shared namespace across calls so earlier definitions
      are available to later executions.
    * Records every execution in :pyattr:`history`.

    Example::

        sb = CodeSandbox()
        result = sb.execute("x = 2 + 2\\nprint(x)")
        assert result.stdout.strip() == "4"
    """

    def __init__(
        self,
        timeout: float = 30.0,
        namespace: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.timeout = timeout
        self._namespace: Dict[str, Any] = namespace if namespace is not None else {}
        self._history: List[ExecutionResult] = []
        self._exec_counter: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(self, code: str) -> ExecutionResult:
        """Compile and execute *code*, returning an :class:`ExecutionResult`."""
        self._exec_counter += 1
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        start = time.monotonic()

        try:
            compiled = compile(code, f"<sandbox-{self._exec_counter}>", "exec")
            with contextlib.redirect_stdout(stdout_buf), \
                 contextlib.redirect_stderr(stderr_buf):
                exec(compiled, self._namespace)  # noqa: S102
            elapsed = time.monotonic() - start

            if elapsed > self.timeout:
                result = ExecutionResult(
                    stdout=stdout_buf.getvalue(),
                    stderr="Execution exceeded timeout",
                    success=False,
                    elapsed=elapsed,
                    exec_id=self._exec_counter,
                )
            else:
                result = ExecutionResult(
                    stdout=stdout_buf.getvalue(),
                    stderr=stderr_buf.getvalue(),
                    success=True,
                    elapsed=elapsed,
                    exec_id=self._exec_counter,
                )
        except Exception:  # noqa: BLE001
            elapsed = time.monotonic() - start
            result = ExecutionResult(
                stdout=stdout_buf.getvalue(),
                stderr=traceback.format_exc(),
                success=False,
                elapsed=elapsed,
                exec_id=self._exec_counter,
            )

        self._history.append(result)
        return result

    def reset(self) -> None:
        """Clear the namespace and history."""
        self._namespace.clear()
        self._history.clear()
        self._exec_counter = 0

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def history(self) -> List[ExecutionResult]:
        """Return a copy of all past execution results."""
        return list(self._history)

    @property
    def last_result(self) -> Optional[ExecutionResult]:
        """Most recent execution result, or *None*."""
        return self._history[-1] if self._history else None

    @property
    def namespace_keys(self) -> List[str]:
        """Names currently defined in the sandbox namespace."""
        return [k for k in self._namespace if not k.startswith("__")]

    @property
    def execution_count(self) -> int:
        return self._exec_counter
