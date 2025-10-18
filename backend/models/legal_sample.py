"""
Legal Sample Model for PostgreSQL Storage.
Replaces parquet file storage with database-backed persistence.
"""

from models.batch import db
from datetime import datetime

class LegalSample(db.Model):
    """
    Legal training sample with question, answer, and metadata.

    Required fields (7):
        - id, question, answer, topic, difficulty, case_citation, reasoning

    Optional fields:
        - jurisdiction, batch_id, sample_type
    """
    __tablename__ = 'legal_samples'

    # Required fields
    id = db.Column(db.String(200), primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    case_citation = db.Column(db.Text, nullable=False)
    reasoning = db.Column(db.Text, nullable=False)

    # Optional fields
    jurisdiction = db.Column(db.String(50), default='uk', nullable=True)
    batch_id = db.Column(db.String(100), nullable=True)
    sample_type = db.Column(db.String(50), default='case_analysis', nullable=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Indexes for common queries
    __table_args__ = (
        db.Index('idx_topic', 'topic'),
        db.Index('idx_difficulty', 'difficulty'),
        db.Index('idx_jurisdiction', 'jurisdiction'),
        db.Index('idx_sample_type', 'sample_type'),
        db.Index('idx_batch_id', 'batch_id'),
        db.Index('idx_created_at', 'created_at'),
    )

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'topic': self.topic,
            'difficulty': self.difficulty,
            'case_citation': self.case_citation,
            'reasoning': self.reasoning,
            'jurisdiction': self.jurisdiction,
            'batch_id': self.batch_id,
            'sample_type': self.sample_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<LegalSample(id='{self.id}', topic='{self.topic}', difficulty='{self.difficulty}')>"
