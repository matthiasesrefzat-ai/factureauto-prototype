import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-in-prod')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE', 50 * 1024 * 1024))
    
    # Parser settings
    PARSERS_ENABLED = ['qonto_pdf', 'qonto_csv', 'brut']
    
    # Invoice settings
    DEFAULT_TVA_RATE = 20
    
    # Security
    MAX_UPLOADS_PER_REQUEST = 10
    ALLOWED_EXTENSIONS = {'pdf', 'csv'}
