"""
Logging system - Write logs to daily files in logs/ directory
"""
import os
import sys
from datetime import datetime
from pathlib import Path

class Logger:
    """Simple logger that writes to daily log files."""
    
    def __init__(self, log_dir="logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_date = None
        self.log_file = None
        self._update_log_file()
    
    def _update_log_file(self):
        """Update log file if date changed."""
        today = datetime.now().date()
        
        if today != self.current_date:
            self.current_date = today
            log_filename = f"firewall_manager_{today.strftime('%Y-%m-%d')}.log"
            self.log_file = self.log_dir / log_filename
    
    def _write(self, level: str, message: str):
        """Write log entry to file and console."""
        self._update_log_file()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # Write to file
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            print(f"Failed to write log: {e}", file=sys.stderr)
        
        # Write to console
        print(log_entry)
    
    def info(self, message: str):
        """Log info message."""
        self._write("INFO", message)
    
    def warning(self, message: str):
        """Log warning message."""
        self._write("WARNING", message)
    
    def error(self, message: str):
        """Log error message."""
        self._write("ERROR", message)
    
    def debug(self, message: str):
        """Log debug message."""
        self._write("DEBUG", message)

# Global logger instance
_logger = None

def get_logger():
    """Get global logger instance."""
    global _logger
    if _logger is None:
        _logger = Logger()
    return _logger

def info(message: str):
    """Log info message."""
    get_logger().info(message)

def warning(message: str):
    """Log warning message."""
    get_logger().warning(message)

def error(message: str):
    """Log error message."""
    get_logger().error(message)

def debug(message: str):
    """Log debug message."""
    get_logger().debug(message)
