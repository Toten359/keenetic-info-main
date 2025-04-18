import os
import csv
import logging
from datetime import datetime
from enum import Enum
import logging


class LogType(Enum):
    FILE = "file"
    CONSOLE = "console"
    BOTH = "both"


class CsvSignalLogHandler(logging.Handler):
    def __init__(self, filename: str = None) -> None:
        super().__init__()
        self.filename = filename
        self._init_file()

    def _init_file(self) -> None:
        new_file = not os.path.exists(self.filename)
        self.file = open(self.filename, "a", newline="")
        self.writer = csv.writer(self.file)
        if new_file:
            self.writer.writerow(["timestamp", "ssid", "rssi", "noise", "rate_mbps", "quality_percent"])

    def emit(self, record: logging.LogRecord) -> None:
        """
        Именно тут мы и пишем в файл
        """
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data = record.msg
            self.writer.writerow(
                [ts, data.get("ssid"), data.get("rssi"), data.get("noise"), data.get("rate"), data.get("quality")]
            )
            self.file.flush()
        except Exception as e:
            self.handleError(record)

    def close(self) -> None:
        super().close()


## TODO: А нужно ли это?


class GenericTextLogHandler(logging.Handler):
    def __init__(self, filename: str = None) -> None:
        super().__init__()
        self.filename = filename if filename is not None else "generic.csv"
        self._init_file()

    def _init_file(self) -> None:
        self.file = open(self.filename, "a", newline="")
        self.writer = csv.writer(self.file)

    def emit(self, record: logging.LogRecord) -> None:
        """
        Именно тут мы и пишем в файл
        """
        if not hasattr(record, "msg"):
            return
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.writer.writerow([ts, record.msg])
            self.file.flush()
        except Exception as e:
            self.handleError(record)

    def close(self) -> None:
        super().close()


def get_logger(
    name, level=logging.INFO, filename: str = None, logType: LogType = None, handler: callable = None
) -> logging.Logger:
    """
    Get a logger with a CSV handler and console handler.
    Args:
        name (str): Name of the logger.
        level (int): Logging level.
        filename (str): CSV file name for logging.
        logType (LogType): Type of logging (e.g., 'file', 'console').
    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(level)
        if logType == LogType.FILE:
            csv_handler = handler(filename)
            logger.addHandler(csv_handler)
        elif logType == LogType.CONSOLE:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            logger.addHandler(console_handler)
        elif logType == LogType.BOTH:
            csv_handler = handler(filename)
            logger.addHandler(csv_handler)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            logger.addHandler(console_handler)
        else:
            raise ValueError("Invalid logType. Must be one of LogType.FILE, LogType.CONSOLE, or LogType.BOTH.")

    return logger
