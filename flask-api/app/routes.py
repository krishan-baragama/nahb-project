"""
Application Routes
"""
from flask import jsonify

def init_routes(app):
    """Initialize all application routes"""
    
    @app.route('/', methods=['GET'])
    def home():
        return jsonify({
            'message': 'Welcome to NAHB API',
            'status': 'running'
        })
    
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'healthy',
            'message': 'API is running'
        })