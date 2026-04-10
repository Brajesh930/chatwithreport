import logging
import json
from pathlib import Path
from datetime import datetime
from helpers.config import Config

class Logger:
    _logger = None

    @classmethod
    def _get_logger(cls):
        """Initialize logger"""
        if cls._logger is not None:
            return cls._logger

        Config.load()
        log_level = Config.get('LOG_LEVEL', 'debug').upper()
        
        # Create logs directory
        storage_path = Path(Config.get('STORAGE_PATH', './storage'))
        logs_dir = storage_path / 'logs'
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Configure logger
        cls._logger = logging.getLogger('DocumentChat')
        cls._logger.setLevel(getattr(logging, log_level, logging.DEBUG))

        # File handler
        log_file = logs_dir / 'app.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level, logging.DEBUG))

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        cls._logger.addHandler(file_handler)
        cls._logger.addHandler(console_handler)

        return cls._logger

    @classmethod
    def info(cls, message, data=None):
        """Log info message"""
        logger = cls._get_logger()
        if data:
            logger.info(f"{message} - {json.dumps(data)}")
        else:
            logger.info(message)

    @classmethod
    def warning(cls, message, data=None):
        """Log warning message"""
        logger = cls._get_logger()
        if data:
            logger.warning(f"{message} - {json.dumps(data)}")
        else:
            logger.warning(message)

    @classmethod
    def error(cls, message, data=None):
        """Log error message"""
        logger = cls._get_logger()
        if data:
            logger.error(f"{message} - {json.dumps(data)}")
        else:
            logger.error(message)

    @classmethod
    def debug(cls, message, data=None):
        """Log debug message"""
        logger = cls._get_logger()
        if data:
            logger.debug(f"{message} - {json.dumps(data)}")
        else:
            logger.debug(message)
