"""Structured logging setup for API and worker processes."""

import json
import logging
import logging.config
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

from backend.app.core.config import Settings
from backend.app.core.request_context import get_request_id


class JsonFormatter(logging.Formatter):
    """Serialize log records into stable, machine-readable JSON."""

    @override
    def formatTime(
        self,
        record: logging.LogRecord,
        datefmt: str | None = None,
    ) -> str:
        """Format timestamps in UTC regardless of host locale."""

        timestamp = datetime.fromtimestamp(record.created, tz=UTC)
        return timestamp.strftime(datefmt or "%Y-%m-%dT%H:%M:%S%z")

    def format(self, record: logging.LogRecord) -> str:
        """Return a JSON log line without serializing sensitive arguments."""

        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
        }
        for field_name in ("method", "path", "status_code", "duration_ms"):
            if hasattr(record, field_name):
                payload[field_name] = getattr(record, field_name)
        request_id = get_request_id()
        if request_id is not None:
            payload["request_id"] = str(request_id)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(settings: Settings) -> None:
    """Load logging configuration, falling back safely if unavailable."""

    config_path = Path(settings.log_config_path)
    if not config_path.is_absolute():
        config_path = Path(__file__).resolve().parents[3] / config_path
    if config_path.is_file():
        with config_path.open(encoding="utf-8") as config_file:
            config: dict[str, Any] = json.load(config_file)
        config["root"]["level"] = settings.log_level
        for handler in config.get("handlers", {}).values():
            handler["level"] = settings.log_level
        for logger_config in config.get("loggers", {}).values():
            logger_config["level"] = settings.log_level
        logging.config.dictConfig(config)
        return

    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
