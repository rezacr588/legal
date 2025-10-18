"""
Data Service for Legal Samples - PostgreSQL ORM Access Layer.

This service provides a clean interface for CRUD operations on legal training samples,
replacing direct parquet file access with database-backed persistence.
"""

from typing import List, Dict, Optional
from models import db, LegalSample
from sqlalchemy import func, or_
from datetime import datetime


class DataService:
    """
    ORM-based data access service for legal training samples.

    Provides methods for:
    - Retrieving samples (all, by ID, filtered, paginated)
    - Adding new samples
    - Updating existing samples
    - Deleting samples
    - Searching and filtering
    - Statistics and aggregations
    """

    def __init__(self, session=None):
        """
        Initialize data service.

        Args:
            session: SQLAlchemy session (optional, uses default if not provided)
        """
        self.session = session or db.session

    # ========================================================================
    # READ OPERATIONS
    # ========================================================================

    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        """
        Get all legal samples.

        Args:
            limit: Maximum number of samples to return (None = all)
            offset: Number of samples to skip

        Returns:
            List of sample dictionaries
        """
        query = self.session.query(LegalSample).order_by(LegalSample.created_at.desc())

        if offset > 0:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        samples = query.all()
        return [sample.to_dict() for sample in samples]

    def get_by_id(self, sample_id: str) -> Optional[Dict]:
        """
        Get a single sample by ID.

        Args:
            sample_id: Sample ID

        Returns:
            Sample dictionary or None if not found
        """
        sample = self.session.query(LegalSample).filter_by(id=sample_id).first()
        return sample.to_dict() if sample else None

    def get_by_batch(self, batch_id: str) -> List[Dict]:
        """
        Get all samples from a specific batch.

        Args:
            batch_id: Batch ID

        Returns:
            List of sample dictionaries
        """
        samples = self.session.query(LegalSample).filter_by(batch_id=batch_id).all()
        return [sample.to_dict() for sample in samples]

    def get_filtered(self,
                    topic: Optional[str] = None,
                    difficulty: Optional[str] = None,
                    jurisdiction: Optional[str] = None,
                    sample_type: Optional[str] = None,
                    limit: Optional[int] = None) -> List[Dict]:
        """
        Get samples matching filter criteria.

        Args:
            topic: Filter by topic
            difficulty: Filter by difficulty
            jurisdiction: Filter by jurisdiction
            sample_type: Filter by sample type
            limit: Maximum number of results

        Returns:
            List of matching sample dictionaries
        """
        query = self.session.query(LegalSample)

        if topic:
            query = query.filter(LegalSample.topic == topic)
        if difficulty:
            query = query.filter(LegalSample.difficulty == difficulty)
        if jurisdiction:
            query = query.filter(LegalSample.jurisdiction == jurisdiction)
        if sample_type:
            query = query.filter(LegalSample.sample_type == sample_type)

        if limit:
            query = query.limit(limit)

        samples = query.all()
        return [sample.to_dict() for sample in samples]

    def search(self, query_text: str, field: str = 'all', limit: int = 100) -> List[Dict]:
        """
        Full-text search across samples.

        Args:
            query_text: Search query
            field: Field to search in ('all', 'question', 'answer', 'topic', 'case_citation')
            limit: Maximum number of results

        Returns:
            List of matching sample dictionaries
        """
        search_pattern = f'%{query_text}%'

        if field == 'all':
            # Search across multiple fields
            filters = or_(
                LegalSample.question.ilike(search_pattern),
                LegalSample.answer.ilike(search_pattern),
                LegalSample.topic.ilike(search_pattern),
                LegalSample.case_citation.ilike(search_pattern)
            )
        else:
            # Search specific field
            if field == 'question':
                filters = LegalSample.question.ilike(search_pattern)
            elif field == 'answer':
                filters = LegalSample.answer.ilike(search_pattern)
            elif field == 'topic':
                filters = LegalSample.topic.ilike(search_pattern)
            elif field == 'case_citation':
                filters = LegalSample.case_citation.ilike(search_pattern)
            else:
                raise ValueError(f'Invalid search field: {field}')

        samples = self.session.query(LegalSample).filter(filters).limit(limit).all()
        return [sample.to_dict() for sample in samples]

    def get_random(self, count: int = 5, difficulty: Optional[str] = None) -> List[Dict]:
        """
        Get random samples.

        Args:
            count: Number of random samples
            difficulty: Optional difficulty filter

        Returns:
            List of random sample dictionaries
        """
        query = self.session.query(LegalSample)

        if difficulty:
            query = query.filter(LegalSample.difficulty == difficulty)

        # Use database random function
        samples = query.order_by(func.random()).limit(count).all()
        return [sample.to_dict() for sample in samples]

    # ========================================================================
    # WRITE OPERATIONS
    # ========================================================================

    def add(self, sample_data: Dict) -> Dict:
        """
        Add a new sample.

        Args:
            sample_data: Dictionary with sample fields

        Returns:
            Created sample dictionary

        Raises:
            ValueError: If required fields are missing or ID already exists
        """
        # Validate required fields
        required_fields = ['id', 'question', 'answer', 'topic', 'difficulty',
                          'case_citation', 'reasoning']
        missing = [f for f in required_fields if f not in sample_data]
        if missing:
            raise ValueError(f'Missing required fields: {", ".join(missing)}')

        # Check for duplicate ID
        existing = self.session.query(LegalSample).filter_by(id=sample_data['id']).first()
        if existing:
            raise ValueError(f'Sample with ID "{sample_data["id"]}" already exists')

        # Handle NULL/empty values with defaults
        case_citation = sample_data.get('case_citation')
        if not case_citation or case_citation == '':
            sample_data['case_citation'] = 'No case citation provided'

        reasoning = sample_data.get('reasoning')
        if not reasoning or reasoning == '':
            sample_data['reasoning'] = 'No reasoning provided'

        # Create new sample
        sample = LegalSample(
            id=sample_data['id'],
            question=sample_data['question'],
            answer=sample_data['answer'],
            topic=sample_data['topic'],
            difficulty=sample_data['difficulty'],
            case_citation=sample_data['case_citation'],
            reasoning=sample_data['reasoning'],
            jurisdiction=sample_data.get('jurisdiction', 'uk'),
            batch_id=sample_data.get('batch_id'),
            sample_type=sample_data.get('sample_type', 'case_analysis')
        )

        self.session.add(sample)
        self.session.commit()

        return sample.to_dict()

    def add_bulk(self, samples_data: List[Dict]) -> Dict:
        """
        Add multiple samples in bulk.

        Args:
            samples_data: List of sample dictionaries

        Returns:
            Dictionary with success count and any errors
        """
        added = 0
        errors = []

        for idx, sample_data in enumerate(samples_data):
            try:
                self.add(sample_data)
                added += 1
            except Exception as e:
                errors.append({
                    'index': idx,
                    'id': sample_data.get('id', 'unknown'),
                    'error': str(e)
                })

        return {
            'added': added,
            'total': len(samples_data),
            'errors': errors
        }

    def update(self, sample_id: str, updates: Dict) -> Dict:
        """
        Update an existing sample.

        Args:
            sample_id: ID of sample to update
            updates: Dictionary with fields to update

        Returns:
            Updated sample dictionary

        Raises:
            ValueError: If sample not found or validation fails
        """
        sample = self.session.query(LegalSample).filter_by(id=sample_id).first()
        if not sample:
            raise ValueError(f'Sample with ID "{sample_id}" not found')

        # If ID is being changed, check for duplicates
        new_id = updates.get('id')
        if new_id and new_id != sample_id:
            existing = self.session.query(LegalSample).filter_by(id=new_id).first()
            if existing:
                raise ValueError(f'Sample with ID "{new_id}" already exists')

        # Update fields
        for field, value in updates.items():
            if hasattr(sample, field):
                setattr(sample, field, value)

        # Update timestamp
        sample.updated_at = datetime.utcnow()

        self.session.commit()
        return sample.to_dict()

    def delete(self, sample_id: str) -> bool:
        """
        Delete a sample.

        Args:
            sample_id: ID of sample to delete

        Returns:
            True if deleted, False if not found
        """
        sample = self.session.query(LegalSample).filter_by(id=sample_id).first()
        if not sample:
            return False

        self.session.delete(sample)
        self.session.commit()
        return True

    # ========================================================================
    # STATISTICS & AGGREGATIONS
    # ========================================================================

    def get_stats(self) -> Dict:
        """
        Get comprehensive dataset statistics.

        Returns:
            Dictionary with statistics
        """
        total = self.session.query(func.count(LegalSample.id)).scalar()

        # Difficulty distribution
        difficulty_counts = self.session.query(
            LegalSample.difficulty,
            func.count(LegalSample.id)
        ).group_by(LegalSample.difficulty).all()

        # Topic distribution (top 10)
        topic_counts = self.session.query(
            LegalSample.topic,
            func.count(LegalSample.id)
        ).group_by(LegalSample.topic).order_by(
            func.count(LegalSample.id).desc()
        ).limit(10).all()

        # Sample type distribution
        sample_type_counts = self.session.query(
            LegalSample.sample_type,
            func.count(LegalSample.id)
        ).group_by(LegalSample.sample_type).all()

        # Jurisdiction distribution
        jurisdiction_counts = self.session.query(
            LegalSample.jurisdiction,
            func.count(LegalSample.id)
        ).group_by(LegalSample.jurisdiction).all()

        # Average text lengths
        avg_lengths = self.session.query(
            func.avg(func.length(LegalSample.question)).label('question'),
            func.avg(func.length(LegalSample.answer)).label('answer'),
            func.avg(func.length(LegalSample.reasoning)).label('reasoning'),
            func.avg(func.length(LegalSample.case_citation)).label('case_citation')
        ).first()

        # Unique counts
        unique_topics = self.session.query(
            func.count(func.distinct(LegalSample.topic))
        ).scalar()

        return {
            'total': total,
            'difficulty_distribution': [
                {'difficulty': d, 'count': c} for d, c in difficulty_counts
            ],
            'top_topics': [
                {'topic': t, 'count': c} for t, c in topic_counts
            ],
            'sample_type_distribution': [
                {'sample_type': st, 'count': c} for st, c in sample_type_counts
            ],
            'jurisdiction_distribution': [
                {'jurisdiction': j, 'count': c} for j, c in jurisdiction_counts
            ],
            'avg_lengths': {
                'question': round(avg_lengths.question or 0, 2),
                'answer': round(avg_lengths.answer or 0, 2),
                'reasoning': round(avg_lengths.reasoning or 0, 2),
                'case_citation': round(avg_lengths.case_citation or 0, 2)
            },
            'unique_topics': unique_topics
        }

    def count(self) -> int:
        """Get total sample count."""
        return self.session.query(func.count(LegalSample.id)).scalar()

    def exists(self, sample_id: str) -> bool:
        """Check if a sample exists."""
        return self.session.query(LegalSample).filter_by(id=sample_id).first() is not None
