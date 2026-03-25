"""Allow running Hermes as ``python -m hermes``."""
from __future__ import annotations

import sys

from hermes.cli import main

sys.exit(main())
