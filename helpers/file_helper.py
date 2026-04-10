import re
import os
import hashlib
from time import time
from pathlib import Path

class FileHelper:
    """Helper functions for file operations"""

    @staticmethod
    def sanitize_filename(filename):
        """Generate safe filename"""
        # Replace spaces with underscores
        filename = re.sub(r'\s+', '_', filename)
        
        # Remove special characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
        
        # Remove multiple dots
        filename = re.sub(r'\.+', '.', filename)
        
        return filename

    @staticmethod
    def get_extension(filename):
        """Get file extension"""
        return Path(filename).suffix.lower().lstrip('.')

    @staticmethod
    def generate_unique_filename(filename):
        """Generate unique filename with timestamp and hash"""
        extension = FileHelper.get_extension(filename)
        basename = Path(filename).stem
        timestamp = int(time())
        random_hash = hashlib.md5(str(time()).encode()).hexdigest()[:8]
        
        return f"{basename}_{timestamp}_{random_hash}.{extension}"

    @staticmethod
    def format_file_size(bytes_size):
        """Get human readable file size"""
        units = ['B', 'KB', 'MB', 'GB']
        bytes_size = max(bytes_size, 0)
        
        if bytes_size == 0:
            pow_val = 0
        else:
            pow_val = int(len(str(bytes_size)) / 3)
        
        pow_val = min(pow_val, len(units) - 1)
        size = bytes_size / (1024 ** pow_val)
        
        return f"{round(size, 2)} {units[pow_val]}"
