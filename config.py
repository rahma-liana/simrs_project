import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'simrs-secret-key-medical-health-2026')
    
    # Konfigurasi Koneksi Database MySQL (Laragon Default)
    MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'db_sistem_rumah_sakit')
    MYSQL_CHARSET = 'utf8mb4'
    
    # Path folder upload / backup
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    BACKUP_FOLDER = os.path.join(BASE_DIR, 'backups')
    
    # Port aplikasi Flask
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't')
