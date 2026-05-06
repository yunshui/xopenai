"""Structured logging utility."""
import json
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        module_line = f"{record.name}:{record.lineno}"
        # Extract client_ip from extra fields if present
        client_ip = record.__dict__.get('client_ip', '-')
        base = f"[{timestamp}] [{record.levelname}] [{module_line}] [{client_ip}] {record.getMessage()}"
        extra = {k: v for k, v in record.__dict__.items()
                 if k not in {'name', 'msg', 'args', 'levelname', 'levelno',
                              'pathname', 'filename', 'module', 'exc_info',
                              'stack_info', 'lineno', 'funcName', 'created',
                              'msecs', 'message', 'asctime', 'exc_text',
                              'relativeCreated', 'thread', 'threadName',
                              'process', 'processName', 'client_ip'}}
        if extra:
            base += f" | {json.dumps(extra)}"
        return base


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def setup_logging(log_dir: str = "logs", level: str = "INFO") -> None:
    level_upper = level.upper()
    if not hasattr(logging, level_upper):
        raise ValueError(f"Invalid log level: {level}")
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(getattr(logging, level_upper))
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(StructuredFormatter())
    root.addHandler(console)
    # Use today's date as log file name
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = Path(log_dir) / f"xopenai-{today}.log"
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=7
    )
    file_handler.setFormatter(StructuredFormatter())
    file_handler.suffix = "%Y-%m-%d.log"
    file_handler.namer = lambda name: name.replace(f"xopenai-{today}.log", f"xopenai-{name.split('.')[-2]}.log") if "." in name else name
    root.addHandler(file_handler)