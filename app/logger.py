"""Structured logging utility."""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        module_line = f"{record.name}:{record.lineno}"
        base = f"[{timestamp}] [{record.levelname}] [{module_line}] {record.getMessage()}"
        extra = {k: v for k, v in record.__dict__.items()
                 if k not in {'name', 'msg', 'args', 'levelname', 'levelno',
                              'pathname', 'filename', 'module', 'exc_info',
                              'stack_info', 'lineno', 'funcName', 'created',
                              'msecs', 'message', 'asctime'}}
        if extra:
            import json
            base += f" | {json.dumps(extra)}"
        return base


_loggers: dict[str, logging.Logger] = {}


def get_logger(name: str) -> logging.Logger:
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
    return _loggers[name]


def setup_logging(log_dir: str = "logs", level: str = "INFO") -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper()))
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(StructuredFormatter())
    root.addHandler(console)
    file_handler = RotatingFileHandler(
        Path(log_dir) / "anthropic2openai.log",
        maxBytes=10*1024*1024, backupCount=7
    )
    file_handler.setFormatter(StructuredFormatter())
    root.addHandler(file_handler)