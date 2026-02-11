"""
WSGI Entry Point for NAHB Flask API
Run with: flask --app wsgi run --debug
"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 NAHB Flask API Server")
    print("=" * 60)
    print("📍 Running on: http://localhost:5000")
    print("📚 API Docs: http://localhost:5000/")
    print("💡 Press CTRL+C to quit")
    print("=" * 60)
    app.run(debug=True, port=5000)