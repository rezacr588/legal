"""
Circuit breaker pattern implementation for handling generation failures gracefully.
Prevents repeated attempts to generate samples for topics that consistently fail.
"""

import time
from typing import Dict, List, Literal

from config import (
    CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
    CIRCUIT_BREAKER_SUCCESS_THRESHOLD
)

CircuitState = Literal['closed', 'open', 'half_open']


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for handling failures gracefully.

    States:
    - CLOSED: Normal operation, failures counted
    - OPEN: Too many failures, block requests
    - HALF-OPEN: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = CIRCUIT_BREAKER_FAILURE_THRESHOLD,
        recovery_timeout: int = CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
        success_threshold: int = CIRCUIT_BREAKER_SUCCESS_THRESHOLD
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit (default: 3)
            recovery_timeout: Seconds to wait before testing recovery (default: 300)
            success_threshold: Successes needed to close circuit (default: 2)
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.circuits: Dict[str, Dict] = {}  # topic -> circuit state

    def get_state(self, topic: str) -> Dict:
        """Get or initialize circuit state for a topic."""
        if topic not in self.circuits:
            self.circuits[topic] = {
                'state': 'closed',
                'failure_count': 0,
                'success_count': 0,
                'last_failure_time': None,
                'opened_at': None
            }
        return self.circuits[topic]

    def is_open(self, topic: str) -> bool:
        """
        Check if circuit is open for a topic.

        Returns:
            True if circuit is open (should skip this topic), False otherwise
        """
        circuit = self.get_state(topic)

        if circuit['state'] == 'closed':
            return False

        if circuit['state'] == 'open':
            # Check if recovery timeout has passed
            if circuit['opened_at']:
                elapsed = time.time() - circuit['opened_at']
                if elapsed >= self.recovery_timeout:
                    # Transition to half-open state
                    circuit['state'] = 'half_open'
                    circuit['success_count'] = 0
                    print(f"🔄 Circuit breaker for '{topic}' transitioned to HALF-OPEN (testing recovery)")
                    return False
            return True

        # half_open state - allow requests through for testing
        return False

    def record_success(self, topic: str) -> None:
        """Record a successful generation attempt."""
        circuit = self.get_state(topic)
        circuit['failure_count'] = 0
        circuit['last_failure_time'] = None

        if circuit['state'] == 'half_open':
            circuit['success_count'] += 1
            if circuit['success_count'] >= self.success_threshold:
                circuit['state'] = 'closed'
                circuit['opened_at'] = None
                print(f"✅ Circuit breaker for '{topic}' CLOSED (recovered)")
        elif circuit['state'] == 'open':
            # Shouldn't happen, but handle it
            circuit['state'] = 'closed'
            circuit['opened_at'] = None
            print(f"✅ Circuit breaker for '{topic}' CLOSED")

    def record_failure(self, topic: str, error: str = None) -> bool:
        """
        Record a failed generation attempt.

        Args:
            topic: The topic that failed
            error: Optional error message

        Returns:
            True if circuit was opened, False otherwise
        """
        circuit = self.get_state(topic)
        circuit['failure_count'] += 1
        circuit['last_failure_time'] = time.time()
        circuit['success_count'] = 0  # Reset success count on failure

        if circuit['state'] == 'half_open':
            # Failed during recovery test - reopen circuit
            circuit['state'] = 'open'
            circuit['opened_at'] = time.time()
            print(f"⛔ Circuit breaker for '{topic}' RE-OPENED (recovery failed)")
            return True

        if circuit['failure_count'] >= self.failure_threshold:
            circuit['state'] = 'open'
            circuit['opened_at'] = time.time()
            print(f"⛔ Circuit breaker for '{topic}' OPENED (threshold reached: {circuit['failure_count']} failures)")
            if error:
                print(f"   Last error: {error}")
            print(f"   Will retry after {self.recovery_timeout} seconds")
            return True

        return False

    def get_summary(self) -> Dict[str, List[Dict]]:
        """
        Get summary of all circuit states.

        Returns:
            Dictionary with open_circuits, half_open_circuits, and closed_with_failures
        """
        summary = {
            'open_circuits': [],
            'half_open_circuits': [],
            'closed_with_failures': []
        }

        for topic, circuit in self.circuits.items():
            if circuit['state'] == 'open':
                elapsed = time.time() - circuit['opened_at'] if circuit['opened_at'] else 0
                summary['open_circuits'].append({
                    'topic': topic,
                    'failures': circuit['failure_count'],
                    'opened_for_seconds': round(elapsed, 1)
                })
            elif circuit['state'] == 'half_open':
                summary['half_open_circuits'].append({
                    'topic': topic,
                    'successes': circuit['success_count']
                })
            elif circuit['failure_count'] > 0:
                summary['closed_with_failures'].append({
                    'topic': topic,
                    'failures': circuit['failure_count']
                })

        return summary

    def reset(self, topic: str = None) -> None:
        """
        Reset circuit breaker state.

        Args:
            topic: Specific topic to reset, or None to reset all
        """
        if topic:
            if topic in self.circuits:
                del self.circuits[topic]
        else:
            self.circuits.clear()
