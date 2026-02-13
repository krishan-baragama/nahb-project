"""
Flask Application Factory
Creates and configures the Flask app
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from app.config import Config
import os

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    CORS(app)
    
    # Create instance folder BEFORE initializing database
    instance_folder = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        'instance'
    )
    os.makedirs(instance_folder, exist_ok=True)
    
    db.init_app(app)
    
    # Import models BEFORE creating tables
    from app import models
    
    with app.app_context():
        db.create_all()
        print("✅ Database initialized")
    
    from app import routes
    routes.init_routes(app)
    
    return app