"""
Batch Manager - Handles concurrent batch generation for multiple providers
"""
import threading
import time
from typing import Dict, Optional
from datetime import datetime
import polars as pl
from pathlib import Path


class BatchManager:
    """Manages multiple concurrent batch generation jobs"""

    def __init__(self):
        self.active_batches: Dict[str, dict] = {}
        self.lock = threading.Lock()
        self.parquet_lock = threading.Lock()  # For thread-safe file writes

    def create_batch(self, batch_id: str, provider: str, model: str,
                    target_count: int, topic_filter: Optional[str] = None,
                    difficulty_filter: Optional[str] = None,
                    reasoning_instruction: Optional[str] = None) -> dict:
        """Create a new batch state"""
        with self.lock:
            batch_state = {
                'running': True,
                'progress': 0,
                'total': 0,
                'current_sample': None,
                'current_provider': provider,
                'current_model': model,
                'errors': [],
                'batch_id': batch_id,
                'started_at': datetime.now().isoformat(),
                'completed_at': None,
                'samples_generated': 0,
                'total_tokens': 0,
                'model_switches': [],
                'provider_switches': [],
                'failed_models_by_provider': {provider: []},
                'consecutive_failures': 0,
                'skipped_topics': [],
                'circuit_breaker_summary': {},
                'topic_filter': topic_filter,
                'difficulty_filter': difficulty_filter,
                'reasoning_instruction': reasoning_instruction,
                'target_count': target_count
            }
            self.active_batches[batch_id] = batch_state
            return batch_state

    def get_batch(self, batch_id: str) -> Optional[dict]:
        """Get a batch state"""
        with self.lock:
            return self.active_batches.get(batch_id)

    def update_batch(self, batch_id: str, updates: dict):
        """Update a batch state"""
        with self.lock:
            if batch_id in self.active_batches:
                self.active_batches[batch_id].update(updates)

    def remove_batch(self, batch_id: str):
        """Remove a completed batch"""
        with self.lock:
            if batch_id in self.active_batches:
                del self.active_batches[batch_id]

    def get_all_batches(self) -> dict:
        """Get all active batches"""
        with self.lock:
            return self.active_batches.copy()

    def is_batch_running(self, batch_id: str) -> bool:
        """Check if a batch is running"""
        with self.lock:
            batch = self.active_batches.get(batch_id)
            return batch and batch.get('running', False)

    def stop_batch(self, batch_id: str):
        """Stop a running batch"""
        with self.lock:
            if batch_id in self.active_batches:
                self.active_batches[batch_id]['running'] = False
                self.active_batches[batch_id]['completed_at'] = datetime.now().isoformat()

    def safe_write_parquet(self, df, path):
        """Thread-safe parquet write"""
        with self.parquet_lock:
            df.write_parquet(path, compression="zstd", statistics=True, use_pyarrow=False)


# Global batch manager instance
_batch_manager = None


def get_batch_manager() -> BatchManager:
    """Get or create the global batch manager"""
    global _batch_manager
    if _batch_manager is None:
        _batch_manager = BatchManager()
    return _batch_manager
