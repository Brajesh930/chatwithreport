import os
from pathlib import Path
from dotenv import load_dotenv

class Config:
    _config = {}
    _loaded = False

    @classmethod
    def load(cls):
        """Load environment configuration from .env file"""
        if cls._loaded:
            return

        # Try to load .env, fall back to .env.example
        env_file = Path(__file__).parent.parent / '.env'
        if not env_file.exists():
            env_file = Path(__file__).parent.parent / '.env.example'

        if env_file.exists():
            load_dotenv(env_file)

        # Load all environment variables
        cls._config = {
            'APP_ENV': os.getenv('APP_ENV', 'development'),
            'APP_NAME': os.getenv('APP_NAME', 'Document Chat System'),
            'AI_PROVIDER': os.getenv('AI_PROVIDER', 'gemini'),
            'AI_API_KEY': os.getenv('AI_API_KEY', ''),
            'AI_MODEL': os.getenv('AI_MODEL', 'gemini-1.5-pro'),
            'MAX_UPLOAD_SIZE': int(os.getenv('MAX_UPLOAD_SIZE', 10485760)),
            'ALLOWED_EXTENSIONS': os.getenv('ALLOWED_EXTENSIONS', 'txt,pdf,docx,md'),
            'STORAGE_PATH': os.getenv('STORAGE_PATH', './storage'),
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'debug')
        }

        cls._loaded = True

    @classmethod
    def get(cls, key, default=None):
        """Get configuration value"""
        if not cls._loaded:
            cls.load()
        return cls._config.get(key, default)

    @classmethod
    def get_all(cls):
        """Get all configuration"""
        if not cls._loaded:
            cls.load()
        return cls._config
