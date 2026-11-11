import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'placement_super_secret_key_change_in_production_2026')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/placement_management')
    DB_NAME = os.getenv('DB_NAME', 'placement_management')
    
    # Upload configuration
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'resumes')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max limit
    ALLOWED_EXTENSIONS = {'pdf'}

    DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
