"""Structured logging for the AI layer.

Uses structlog (already a dependency) so AI call records are JSON-shaped:
their key-value pairs survive grep / log aggregation. Falls back to stdlib
logging if structlog isn't initialized.
"""

from __future__ import annotations

import logging

try:
    import structlog

    _structlog_available = True
except ImportError:  # pragma: no cover
    _structlog_available = False


def get_ai_logger(name: str = "skillshub.ai"):
    """Return a structlog BoundLogger when available, else a stdlib Logger.

    Both share the same `.info(msg, **kv)` calling convention thanks to
    structlog's stdlib bridge; consumers don't need to branch on which.
    """
    if _structlog_available:
        return structlog.get_logger(name)
    return logging.getLogger(name)
