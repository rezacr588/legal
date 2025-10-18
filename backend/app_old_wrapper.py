"""
Backend API Server - Main application entry point.
Temporary wrapper around existing api_server until full refactoring is complete.
"""
import sys
from pathlib import Path

# Add legal-dashboard directory to path (mounted from archive in Docker)
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir / "legal-dashboard"))

# Import and run the existing API server
import api_server
app = api_server.app

if __name__ == '__main__':
    print("="*80)
    print("🚀 Starting Backend API Server")
    print("="*80)
    print(f"Backend directory: {Path(__file__).parent}")
    print(f"Data directory: {Path(__file__).parent / 'data'}")
    print(f"Server: http://localhost:5000")
    print("="*80)

    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
