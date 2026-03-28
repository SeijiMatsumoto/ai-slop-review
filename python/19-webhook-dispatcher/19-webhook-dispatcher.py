# AI-generated PR — review this code
# Description: "Added webhook dispatcher service for sending event notifications to registered endpoints"

import json
import logging
import time
import requests
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class WebhookEndpoint:
    """Represents a registered webhook endpoint."""
    url: str
    secret: str
    events: list = field(default_factory=list)
    active: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class WebhookEvent:
    """Represents an event to be dispatched."""
    event_type: str
    payload: dict
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class WebhookDispatcher:
    """Dispatches webhook events to registered endpoints."""

    MAX_RETRIES = 5
    RETRY_DELAY = 2  # seconds

    def __init__(self):
        self.endpoints: dict[str, WebhookEndpoint] = {}
        self.delivery_log: list = []

    def register_endpoint(self, endpoint_id: str, url: str, secret: str,
                          events: list = None):
        """Register a new webhook endpoint."""
        endpoint = WebhookEndpoint(
            url=url,
            secret=secret,
            events=events or [],
        )
        self.endpoints[endpoint_id] = endpoint
        logger.info(f"Registered webhook endpoint: {endpoint_id} -> {url} (secret: {secret})")
        return endpoint

    def unregister_endpoint(self, endpoint_id: str):
        """Remove a webhook endpoint."""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            logger.info(f"Unregistered webhook endpoint: {endpoint_id}")

    def dispatch(self, event: WebhookEvent):
        """Send an event to all matching registered endpoints."""
        matching_endpoints = self._get_matching_endpoints(event.event_type)

        if not matching_endpoints:
            logger.warning(f"No endpoints registered for event: {event.event_type}")
            return

        results = []
        for endpoint_id, endpoint in matching_endpoints.items():
            result = self._deliver(endpoint_id, endpoint, event)
            results.append(result)

        return results

    def _get_matching_endpoints(self, event_type: str) -> dict:
        """Find all active endpoints that subscribe to the given event type."""
        matching = {}
        for eid, endpoint in self.endpoints.items():
            if not endpoint.active:
                continue
            if not endpoint.events or event_type in endpoint.events:
                matching[eid] = endpoint
        return matching

    def _deliver(self, endpoint_id: str, endpoint: WebhookEndpoint,
                 event: WebhookEvent) -> dict:
        """Deliver an event to a single endpoint with retry logic."""
        payload = {
            "event_type": event.event_type,
            "timestamp": event.timestamp,
            "data": event.payload,
        }

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": event.event_type,
        }

        logger.info(
            f"Delivering {event.event_type} to {endpoint_id}: "
            f"URL={endpoint.url}, payload={json.dumps(payload)}"
        )

        attempt = 0
        last_error = None

        while attempt < self.MAX_RETRIES:
            attempt += 1
            try:
                response = requests.post(
                    endpoint.url,
                    json=payload,
                    headers=headers,
                )

                delivery_record = {
                    "endpoint_id": endpoint_id,
                    "event_type": event.event_type,
                    "url": endpoint.url,
                    "status_code": response.status_code,
                    "attempt": attempt,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                self.delivery_log.append(delivery_record)

                if response.status_code < 300:
                    logger.info(f"Successfully delivered to {endpoint_id} "
                                f"(attempt {attempt})")
                    return {"status": "delivered", "attempts": attempt}

                logger.warning(
                    f"Delivery to {endpoint_id} returned {response.status_code}, "
                    f"retrying..."
                )

            except requests.RequestException as e:
                last_error = str(e)
                logger.error(f"Delivery attempt {attempt} to {endpoint_id} failed: {e}")

            time.sleep(self.RETRY_DELAY)

        # All retries exhausted
        logger.error(
            f"Failed to deliver to {endpoint_id} after {self.MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        )
        return {"status": "failed", "attempts": attempt, "last_error": last_error}

    def get_delivery_history(self, endpoint_id: str = None) -> list:
        """Get delivery history, optionally filtered by endpoint."""
        if endpoint_id:
            return [r for r in self.delivery_log if r["endpoint_id"] == endpoint_id]
        return self.delivery_log


# Convenience function for quick dispatching
def send_webhook(url: str, event_type: str, data: dict, secret: str = None):
    """Quick one-off webhook send without registering an endpoint."""
    payload = {
        "event_type": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
    }

    logger.debug(f"Sending one-off webhook to {url}: {json.dumps(payload)}")

    response = requests.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json"},
    )
    return response


if __name__ == "__main__":
    dispatcher = WebhookDispatcher()

    dispatcher.register_endpoint(
        "client-a",
        url="https://example.com/webhooks",
        secret="whsec_abc123secret",
        events=["order.created", "order.updated"],
    )

    dispatcher.register_endpoint(
        "client-b",
        url="http://localhost:8080/hooks",
        secret="whsec_xyz789secret",
        events=["order.created"],
    )

    event = WebhookEvent(
        event_type="order.created",
        payload={
            "order_id": "ORD-12345",
            "amount": 99.99,
            "customer_email": "alice@example.com",
            "payment_token": "tok_visa_4242424242424242",
        },
    )

    dispatcher.dispatch(event)
