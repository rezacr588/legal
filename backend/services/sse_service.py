"""
SSE (Server-Sent Events) Service - Real-time batch update broadcasting.
Decoupled from routes layer to avoid circular imports.
"""
import json
import queue
from typing import Optional, Dict


class SSEService:
    """
    Service for managing Server-Sent Events (SSE) broadcasting.
    Allows batch_service to broadcast updates without circular import dependencies.
    """

    def __init__(self):
        self.subscribers = []

    def add_subscriber(self, subscriber: queue.Queue):
        """Add a new SSE subscriber queue"""
        if subscriber not in self.subscribers:
            self.subscribers.append(subscriber)

    def remove_subscriber(self, subscriber: queue.Queue):
        """Remove an SSE subscriber"""
        if subscriber in self.subscribers:
            self.subscribers.remove(subscriber)

    def broadcast_batch_update(self, batch_id: str = None, batch_data: Dict = None):
        """
        Broadcast batch update to all SSE subscribers.

        Args:
            batch_id: Batch ID to broadcast (if None, broadcasts all batches)
            batch_data: Pre-fetched batch data (REQUIRED for reliable broadcasts)
                       Avoids creating new BatchService instance which has empty active_batches
        """
        if batch_id and batch_data:
            # Use provided batch data (most reliable - from active batch worker)
            data = {'type': 'batch_update', 'batch_id': batch_id, 'batch': batch_data}
        elif batch_id and not batch_data:
            # Fallback: fetch batch data (less reliable due to instance issue)
            from services.batch_service import BatchService
            batch_service = BatchService()
            batch = batch_service.get_batch(batch_id)
            if batch:
                data = {'type': 'batch_update', 'batch_id': batch_id, 'batch': batch}
            else:
                return  # Batch not found, skip broadcast
        else:
            # Broadcast all active batches
            from services.batch_service import BatchService
            batch_service = BatchService()
            batches = batch_service.get_running_batches()
            data = {'type': 'all_batches', 'batches': batches}

        message = f"data: {json.dumps(data)}\n\n"

        # Send to all subscribers, remove disconnected ones
        active_subscribers = []
        for subscriber in self.subscribers:
            try:
                subscriber.put_nowait(message)
                active_subscribers.append(subscriber)
            except:
                pass  # Subscriber disconnected or queue full

        self.subscribers = active_subscribers


# Global singleton instance
_sse_service_instance = None

def get_sse_service() -> SSEService:
    """Get the global SSE service singleton instance"""
    global _sse_service_instance
    if _sse_service_instance is None:
        _sse_service_instance = SSEService()
    return _sse_service_instance
