"""
Configuration for Flask Application
"""
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv()

class Config:
    """Flask configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir, '../instance/stories.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Key for protecting write endpoints (Level 16+)
    API_KEY = os.environ.get('API_KEY') or 'dev-api-key-12345'