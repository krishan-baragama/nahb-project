"""
Flask Application Factory
Creates and configures the Flask app
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from app.config import Config
import os

# Initialize extensions
db = SQLAlchemy()

def create_app(config_class=Config):
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    CORS(app)
    db.init_app(app)
    
    # Ensure instance folder exists
    instance_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        print("✅ Database initialized successfully!")
    
    # Register routes
    from app import routes
    routes.init_routes(app)
    
    return app