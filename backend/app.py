"""
Legal Training Dataset API - PostgreSQL Backend
Main Flask application with ORM-based data access.
"""

import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from flask import Flask, jsonify
from flask_cors import CORS
from models import db
from config import DATABASE_URI
from routes.data_routes import data_bp
from routes.generation_routes import generation_bp
from routes.provider_routes import provider_bp
from routes.chat_routes import chat_bp
import os

# Create Flask app
app = Flask(__name__)

# CORS configuration
CORS(app,
     resources={r"/api/*": {"origins": "*"}},
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=False)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Initialize SQLAlchemy
db.init_app(app)

# Register blueprints
app.register_blueprint(data_bp)
app.register_blueprint(generation_bp)
app.register_blueprint(provider_bp)
app.register_blueprint(chat_bp)

# Create tables on startup
with app.app_context():
    db.create_all()
    print("✅ Database tables created/verified")


# ============================================================================
# HEALTH CHECK & INFO ROUTES
# ============================================================================

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'

    # Get sample count
    try:
        from services.data_service import DataService
        service = DataService()
        total_samples = service.count()
    except:
        total_samples = 'unknown'

    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'database_uri': DATABASE_URI.split('@')[1] if '@' in DATABASE_URI else 'local',
        'total_samples': total_samples,
        'groq_configured': bool(os.getenv('GROQ_API_KEY')),
        'cerebras_configured': bool(os.getenv('CEREBRAS_API_KEY'))
    })


@app.route('/api/info')
def get_info():
    """Get API information and available endpoints."""
    return jsonify({
        'name': 'Legal Training Dataset API',
        'version': '2.0.0',
        'database': 'PostgreSQL',
        'architecture': 'ORM-based (SQLAlchemy)',
        'endpoints': {
            'data': [
                'GET /api/data - Get all samples',
                'GET /api/stats - Get statistics',
                'POST /api/add - Add single sample',
                'POST /api/import/jsonl - Import multiple samples',
                'GET /api/sample/<id> - Get sample by ID',
                'PUT /api/sample/<id> - Update sample',
                'DELETE /api/sample/<id> - Delete sample',
                'GET /api/search - Full-text search',
                'GET /api/samples/random - Get random samples',
                'GET /api/samples/filter - Get filtered samples',
                'GET /api/batch/<id>/samples - Get batch samples'
            ],
            'generation': [
                'POST /api/generate - Generate single sample',
                'POST /api/generate/batch/start - Start batch generation',
                'POST /api/generate/batch/stop - Stop batch generation',
                'GET /api/generate/batch/status - Get batch status',
                'GET /api/generate/batch/history - Get batch history',
                'GET /api/generate/batch/stream - SSE stream for updates',
                'GET /api/batches/stuck - Check for stuck batches',
                'GET /api/models - Get available models',
                'GET /api/providers - Get available providers',
                'GET /api/sample-types - Get sample types',
                'GET /api/topics - Get available topics'
            ],
            'health': [
                'GET /api/health - Health check',
                'GET /api/info - API information'
            ]
        }
    })


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    db.session.rollback()
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 Legal Training Dataset API - PostgreSQL Backend")
    print("=" * 80)
    print(f"Database: {DATABASE_URI.split('@')[1] if '@' in DATABASE_URI else 'local'}")
    print(f"Server: http://localhost:5000")
    print("=" * 80)

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True,
        use_reloader=True  # Auto-reload enabled for development
    )
