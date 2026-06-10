import logging
import os
from datetime import datetime
from app.config_manager import get_logs_dir, get_log_level

# 日志级别映射
LOG_LEVELS = {
    'debug': logging.DEBUG,
    'verbose': logging.DEBUG,  # verbose 使用 debug 级别
    'info': logging.INFO,
    'warn': logging.WARNING,
    'error': logging.ERROR,
}

class Logger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.logger = None
        self.file_handler = None
        self.console_handler = None
        self.current_log_date = None
        self.setup_logger()
        self._initialized = True
    
    def get_today_log_filename(self):
        """Generate log filename based on today's date"""
        return f"app_{datetime.now().strftime('%Y%m%d')}.log"
    
    def _get_log_level(self):
        """Get log level from config"""
        level_str = get_log_level()
        return LOG_LEVELS.get(level_str, logging.INFO)
    
    def setup_logger(self):
        """Setup logger with file and console handlers"""
        # Create logger
        self.logger = logging.getLogger('ytdlp-webui')
        self.logger.setLevel(logging.DEBUG)  # Set to lowest level, handlers will filter
        self.logger.propagate = False
        
        # Clear existing handlers if any
        self.logger.handlers.clear()
        
        # Create logs directory if not exists
        logs_dir = get_logs_dir()
        
        # Create file handler with date (daily rotation)
        log_filename = self.get_today_log_filename()
        log_filepath = os.path.join(logs_dir, log_filename)
        
        # Use append mode to continue writing to the same file for the day
        self.file_handler = logging.FileHandler(log_filepath, mode='a', encoding='utf-8')
        self.file_handler.setLevel(self._get_log_level())
        self.current_log_date = datetime.now().date()
        
        # Create console handler
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(self._get_log_level())
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.file_handler.setFormatter(formatter)
        self.console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.console_handler)
    
    def _check_rotation(self):
        """Check if we need to rotate log file (new day)"""
        today = datetime.now().date()
        if self.current_log_date != today:
            self.reopen_file()
    
    def close_file(self):
        """Close current log file handler"""
        if self.file_handler:
            self.logger.removeHandler(self.file_handler)
            self.file_handler.close()
            self.file_handler = None
            self.current_log_date = None
    
    def reopen_file(self):
        """Open a new log file (for current day)"""
        if self.file_handler:
            self.close_file()
        
        # Create new file handler
        logs_dir = get_logs_dir()
        log_filename = self.get_today_log_filename()
        log_filepath = os.path.join(logs_dir, log_filename)
        
        # Use append mode to continue writing to the same file for the day
        self.file_handler = logging.FileHandler(log_filepath, mode='a', encoding='utf-8')
        self.file_handler.setLevel(self._get_log_level())
        self.current_log_date = datetime.now().date()
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.file_handler.setFormatter(formatter)
        self.logger.addHandler(self.file_handler)
    
    def set_log_level(self, level_str: str):
        """Update log level dynamically"""
        level = LOG_LEVELS.get(level_str, logging.INFO)
        if self.file_handler:
            self.file_handler.setLevel(level)
        if self.console_handler:
            self.console_handler.setLevel(level)
    
    def debug(self, message):
        self._check_rotation()
        self.logger.debug(message)
    
    def info(self, message):
        self._check_rotation()
        self.logger.info(message)
    
    def warning(self, message):
        self._check_rotation()
        self.logger.warning(message)
    
    def error(self, message):
        self._check_rotation()
        self.logger.error(message)
    
    def exception(self, message):
        self._check_rotation()
        self.logger.exception(message)


# Create global logger instance
app_logger = Logger()
