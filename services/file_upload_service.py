import os
from pathlib import Path
from werkzeug.utils import secure_filename
from helpers.config import Config
from helpers.logger import Logger
from helpers.file_helper import FileHelper

class FileUploadService:
    """Service for handling file uploads"""

    def __init__(self):
        Config.load()
        self.max_size = Config.get('MAX_UPLOAD_SIZE', 10485760)  # 10MB default
        allowed_str = Config.get('ALLOWED_EXTENSIONS', 'txt,pdf,docx,md')
        self.allowed_extensions = [ext.strip() for ext in allowed_str.split(',')]
        
        storage_path = Path(Config.get('STORAGE_PATH', './storage'))
        self.upload_dir = storage_path / 'uploads'
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate(self, file_obj):
        """Validate uploaded file"""
        if not file_obj:
            return {'valid': False, 'error': 'No file uploaded'}

        # Check file size
        file_obj.seek(0, os.SEEK_END)
        file_size = file_obj.tell()
        file_obj.seek(0)

        if file_size > self.max_size:
            return {
                'valid': False,
                'error': f"File exceeds maximum size of {FileHelper.format_file_size(self.max_size)}"
            }

        # Check file extension
        filename = file_obj.filename or ''
        extension = FileHelper.get_extension(filename)
        if extension not in self.allowed_extensions:
            allowed_types = ', '.join(self.allowed_extensions)
            return {
                'valid': False,
                'error': f'File type not allowed. Allowed types: {allowed_types}'
            }

        return {'valid': True}

    def process(self, file_obj, original_filename=None):
        """Process uploaded file"""
        if not file_obj:
            return {'success': False, 'error': 'No file uploaded'}

        # Validate
        validation = self.validate(file_obj)
        if not validation['valid']:
            return {'success': False, 'error': validation['error']}

        # Get original filename
        if not original_filename:
            original_filename = file_obj.filename

        # Generate safe filename
        safe_name = FileHelper.sanitize_filename(original_filename)
        unique_name = FileHelper.generate_unique_filename(safe_name)
        upload_path = self.upload_dir / unique_name

        try:
            file_obj.seek(0)
            file_obj.save(str(upload_path))
            
            Logger.info('File uploaded successfully', {
                'original_filename': original_filename,
                'stored_filename': unique_name,
                'size': upload_path.stat().st_size
            })

            return {
                'success': True,
                'original_filename': original_filename,
                'stored_filename': unique_name,
                'upload_path': str(upload_path)
            }
        except Exception as e:
            Logger.error('File upload failed', {'error': str(e)})
            return {'success': False, 'error': f'Failed to save file: {str(e)}'}
