"""
Database models for batch management.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class BatchHistory(db.Model):
    """
    Model for tracking batch generation history.
    Stores metadata about batch generation jobs including progress, errors, and model switches.
    """
    __tablename__ = 'batch_history'

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
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

    def to_dict(self):
        """Convert batch to dictionary for API responses."""
        import json
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

    def __repr__(self):
        return f'<BatchHistory {self.batch_id}>'
