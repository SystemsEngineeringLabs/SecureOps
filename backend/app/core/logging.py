import logging
import re
import sys

import structlog

from app.core.config import settings
from app.core.tenant_context import get_tenant_or_none

_SENSITIVE_PATTERN = re.compile(
    r"(password|token|secret|credential|authorization)", re.IGNORECASE
)


def _redact_sensitive(
    _logger: object, _method: str, event_dict: dict
) -> dict:
    for key in list(event_dict.keys()):
        if isinstance(key, str) and _SENSITIVE_PATTERN.search(key):
            event_dict[key] = "[REDACTED]"
    return event_dict


def _add_tenant_context(
    _logger: object, _method: str, event_dict: dict
) -> dict:
    tenant_id = get_tenant_or_none()
    if tenant_id is not None:
        event_dict.setdefault("tenant_id", str(tenant_id))
    return event_dict


def setup_logging() -> None:
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        _add_tenant_context,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        _redact_sensitive,
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.LOG_FORMAT == "json":
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
