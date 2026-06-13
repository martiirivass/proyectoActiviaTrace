import logging
import sys
from pythonjsonlogger import jsonlogger


class StructuredJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = record.created
        log_record["level"] = record.levelname
        log_record["message"] = record.getMessage()

        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName", "relativeCreated",
                "thread", "threadName", "exc_info", "exc_text", "stack_info",
                "timestamp", "level"
            }:
                log_record[key] = value


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = StructuredJsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s",
        timestamp=True,
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.error").handlers.clear()
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)