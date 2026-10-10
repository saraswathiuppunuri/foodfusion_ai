import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get('SECRET_KEY', 'foodai-super-secret-key-2026')
    
    # MySQL connection string format:
    # mysql+pymysql://<user>:<password>@<host>:<port>/<dbname>
    # If MYSQL_URL is not set or fails, falls back gracefully to local SQLite
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'food_ordering_ai')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    
    # Priority: explicit DATABASE_URL -> constructed MySQL URL -> SQLite fallback
    DEFAULT_MYSQL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # OpenStreetMap is free & default; optional Google Maps API Key
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
