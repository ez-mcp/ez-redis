"""ez-redis: Redis expertise for AI coding agents.

Importing this package is deliberately near-zero cost: the hook hot path
(parent plan §14, Phase 34) imports ``ez_redis`` once per hook invocation,
so nothing heavy may be pulled in at package import time.
"""

from typing import Final

__version__: Final[str] = "0.1.0"

__all__ = ["__version__"]
