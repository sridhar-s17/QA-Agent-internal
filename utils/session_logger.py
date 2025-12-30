"""
Session Logger - Session-aware logging utilities
Similar to uno-mcp's logger.py but for QA sessions
"""

import logging
import os
from typing import Dict, Optional, List, Any
from datetime import datetime
from pathlib import Path

class SessionLogHandler(logging.FileHandler):
    """
    Custom logging handler that routes log records to session-specific files
    Similar to uno-mcp's SessionLogHandler
    """
    
    def __init__(self, session_uuid: str, logs_dir: str, log_level: str = "INFO"):
        """
        Initialize session log handler
        
        Args:
            session_uuid (str): Session UUID for log file naming
            logs_dir (str): Directory for log files
            log_level (str): Logging level
        """
        self.session_uuid = session_uuid
        self.logs_dir = logs_dir
        
        # Ensure logs directory exists
        Path(logs_dir).mkdir(parents=True, exist_ok=True)
        
        # Create session-specific log file
        log_filename = f"{session_uuid}.log"
        log_filepath = os.path.join(logs_dir, log_filename)
        
        # Initialize file handler
        super().__init__(log_filepath, encoding='utf-8')
        
        # Set log level
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.setLevel(level)
        
        # Set formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - (Session: %(session_id)s) - %(name)s - %(message)s'
        )
        self.setFormatter(formatter)
    
    def emit(self, record):
        """
        Emit log record with session context
        
        Args:
            record: Log record to emit
        """
        # Add session ID to record only if not already present
        if not hasattr(record, 'session_id'):
            record.session_id = self.session_uuid
        
        super().emit(record)

class SessionLogger:
    """
    Session-aware logger that creates session-specific log files
    """
    
    def __init__(self, session_uuid: str, logs_dir: str, logger_name: str = None):
        """
        Initialize session logger
        
        Args:
            session_uuid (str): Session UUID
            logs_dir (str): Directory for log files
            logger_name (str): Logger name (optional)
        """
        self.session_uuid = session_uuid
        self.logs_dir = logs_dir
        self.logger_name = logger_name or f"QASession.{session_uuid}"
        
        # Create logger
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            # Add session-specific file handler
            session_handler = SessionLogHandler(session_uuid, logs_dir)
            self.logger.addHandler(session_handler)
            
            # Add console handler for immediate feedback
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def _add_session_context(self):
        """Add session context to all log records"""
        # Store the original factory
        original_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = original_factory(*args, **kwargs)
            # Only set session_id if it doesn't already exist
            if not hasattr(record, 'session_id'):
                record.session_id = self.session_uuid
            return record
        
        # Only set the factory if it hasn't been set for this session already
        if not hasattr(logging, '_qa_session_factory_set'):
            logging.setLogRecordFactory(record_factory)
            logging._qa_session_factory_set = True
    
    
    def info(self, message: str, **kwargs):
        """Log info message with session context"""
        self.logger.info(f"[{self.session_uuid}] {message}", **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with session context"""
        self.logger.debug(f"[{self.session_uuid}] {message}", **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with session context"""
        self.logger.warning(f"[{self.session_uuid}] {message}", **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with session context"""
        self.logger.error(f"[{self.session_uuid}] {message}", **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with session context"""
        self.logger.critical(f"[{self.session_uuid}] {message}", **kwargs)
    
    def get_log_file_path(self) -> str:
        """
        Get the path to the session log file
        
        Returns:
            str: Path to log file
        """
        return os.path.join(self.logs_dir, f"{self.session_uuid}.log")

def setup_session_logger(session_uuid: str, logs_dir: str, logger_name: str = None) -> SessionLogger:
    """
    Setup session-specific logger
    Similar to uno-mcp's setup_session_logger function
    
    Args:
        session_uuid (str): Session UUID
        logs_dir (str): Directory for log files
        logger_name (str): Logger name (optional)
        
    Returns:
        SessionLogger: Configured session logger
    """
    return SessionLogger(session_uuid, logs_dir, logger_name)

def get_session_logs(session_uuid: str, logs_dir: str, lines: int = None) -> Optional[str]:
    """
    Get log content for a specific session
    
    Args:
        session_uuid (str): Session UUID
        logs_dir (str): Directory containing log files
        lines (int): Number of lines to return (None for all)
        
    Returns:
        Optional[str]: Log content or None if file not found
    """
    try:
        log_file_path = os.path.join(logs_dir, f"{session_uuid}.log")
        
        if not os.path.exists(log_file_path):
            return None
        
        with open(log_file_path, 'r', encoding='utf-8') as f:
            if lines:
                # Read last N lines
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
            else:
                # Read all lines
                return f.read()
                
    except Exception as e:
        logging.error(f"Error reading session logs for {session_uuid}: {e}")
        return None

def list_session_log_files(logs_dir: str) -> List[Dict[str, Any]]:
    """
    List all session log files in directory
    
    Args:
        logs_dir (str): Directory containing log files
        
    Returns:
        List[Dict[str, Any]]: List of log file information
    """
    try:
        log_files = []
        
        if not os.path.exists(logs_dir):
            return log_files
        
        for filename in os.listdir(logs_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(logs_dir, filename)
                session_uuid = filename[:-4]  # Remove .log extension
                
                # Get file stats
                stat = os.stat(filepath)
                
                log_info = {
                    "session_uuid": session_uuid,
                    "filename": filename,
                    "filepath": filepath,
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
                
                log_files.append(log_info)
        
        # Sort by modified time (most recent first)
        log_files.sort(key=lambda x: x["modified_at"], reverse=True)
        
        return log_files
        
    except Exception as e:
        logging.error(f"Error listing session log files: {e}")
        return []

def cleanup_old_log_files(logs_dir: str, days_old: int = 30) -> int:
    """
    Cleanup old log files
    
    Args:
        logs_dir (str): Directory containing log files
        days_old (int): Remove files older than this many days
        
    Returns:
        int: Number of files removed
    """
    try:
        from datetime import timedelta
        
        if not os.path.exists(logs_dir):
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        removed_count = 0
        
        for filename in os.listdir(logs_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(logs_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                
                if file_time < cutoff_date:
                    os.remove(filepath)
                    removed_count += 1
        
        return removed_count
        
    except Exception as e:
        logging.error(f"Error cleaning up old log files: {e}")
        return 0