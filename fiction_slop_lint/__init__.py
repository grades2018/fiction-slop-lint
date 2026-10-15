"""fiction-slop-lint: an offline style linter for fiction manuscripts."""

__version__ = "0.1.0"

from .engine import analyze, analyze_files  # noqa: E402,F401
from .rules import load_rules  # noqa: E402,F401

__all__ = ["__version__", "analyze", "analyze_files", "load_rules"]
