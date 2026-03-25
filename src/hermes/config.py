"""Configuration management with environment variable overrides."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HermesConfig:
    """Application configuration.

    Every field can be overridden by the corresponding ``HERMES_``-prefixed
    environment variable (e.g. ``HERMES_TIMEOUT`` sets *timeout*).
    """

    timeout: float = 30.0
    max_retries: int = 2
    log_level: str = "INFO"
    sandbox_enabled: bool = True
    agent_name: str = "Hermes"
    max_steps: int = 50

    def __post_init__(self) -> None:
        self.timeout = float(os.getenv("HERMES_TIMEOUT", str(self.timeout)))
        self.max_retries = int(os.getenv("HERMES_MAX_RETRIES", str(self.max_retries)))
        self.log_level = os.getenv("HERMES_LOG_LEVEL", self.log_level)
        self.sandbox_enabled = os.getenv(
            "HERMES_SANDBOX_ENABLED", str(self.sandbox_enabled)
        ).lower() in ("true", "1", "yes")
        self.agent_name = os.getenv("HERMES_AGENT_NAME", self.agent_name)
        self.max_steps = int(os.getenv("HERMES_MAX_STEPS", str(self.max_steps)))
