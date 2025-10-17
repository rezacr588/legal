"""
Database models for batch history tracking.
Uses SQLAlchemy ORM for persistence.
"""

import json
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()


class BatchHistory(db.Model):
    """
    Tracks batch generation history and metadata.

    Stores information about each batch generation run including:
    - Batch configuration (model, filters, target)
    - Progress metrics (samples generated, tokens used)
    - Status tracking (running, completed, stopped)
    - Error logs and model switches
    """

    __tablename__ = 'batch_history'

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.String(100), unique=True, nullable=False)
    started_at = db.Column(db.String(50), nullable=False)
    completed_at = db.Column(db.String(50))
    model = db.Column(db.String(100))
    topic_filter = db.Column(db.String(200))
    difficulty_filter = db.Column(db.String(50))
    reasoning_instruction = db.Column(db.Text)
    target_count = db.Column(db.Integer)
    samples_generated = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20))  # running, completed, stopped
    errors = db.Column(db.Text)  # JSON string
    model_switches = db.Column(db.Text)  # JSON string tracking model switches

    def to_dict(self) -> dict:
        """
        Convert batch history record to dictionary.

        Returns:
            Dictionary representation of the batch
        """
        return {
            'id': self.batch_id,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'model': self.model,
            'topic_filter': self.topic_filter,
            'difficulty_filter': self.difficulty_filter,
            'reasoning_instruction': self.reasoning_instruction,
            'target': self.target_count,
            'samples_generated': self.samples_generated,
            'tokens_used': self.total_tokens,
            'status': self.status,
            'errors': json.loads(self.errors) if self.errors else [],
            'model_switches': json.loads(self.model_switches) if self.model_switches else []
        }


def init_db(app):
    """
    Initialize database with Flask app.

    Args:
        app: Flask application instance
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()
