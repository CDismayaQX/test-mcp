from __future__ import annotations

import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)

_logger = structlog.get_logger()


class Log:
    @staticmethod
    def debug(event: str, **kw: object) -> None:
        _logger.debug(event, **kw)

    @staticmethod
    def info(event: str, **kw: object) -> None:
        _logger.info(event, **kw)

    @staticmethod
    def warning(event: str, **kw: object) -> None:
        _logger.warning(event, **kw)

    @staticmethod
    def error(event: str, **kw: object) -> None:
        _logger.error(event, **kw)

    @staticmethod
    def exception(event: str, **kw: object) -> None:
        _logger.exception(event, **kw)
