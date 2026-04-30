# Review this code — find bugs, understand the logic, complete the TODOs
#
# Domain:
#   Channel: delivery method — "email", "sms", or "push"
#   Message type: the kind of notification (e.g. "order_shipped", "password_reset", "promo")
#   Throttle / cooldown: suppress repeat notifications of the same kind to the same user
#     within a time window, to avoid spamming them

import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Notification:
    notification_id: str
    user_id: str
    channel: str          # "email" | "sms" | "push"
    message_type: str     # e.g. "order_shipped", "password_reset", "promo"
    body: str
    timestamp: float = field(default_factory=time.time)


class NotificationDispatcher:
    def __init__(self, cooldown_seconds: float = 60.0) -> None:
        self.cooldown_seconds = cooldown_seconds
        self._last_sent: dict[tuple, float] = {}
        self._sent: list[Notification] = []
        self._suppressed: list[Notification] = []

    def _throttle_key(self, n: Notification) -> tuple:
        return (n.user_id, n.channel)

    def _is_throttled(self, n: Notification) -> bool:
        key = self._throttle_key(n)
        last = self._last_sent.get(key)
        if last is None:
            return False
        return time.time() - last > self.cooldown_seconds

    def dispatch(self, notification: Notification) -> bool:
        if self._is_throttled(notification):
            self._suppressed.append(notification)
            return False
        key = self._throttle_key(notification)
        self._last_sent[key] = notification.timestamp
        self._sent.append(notification)
        return True

    def dispatch_batch(self, notifications: list[Notification]) -> dict[str, bool]:
        return {n.notification_id: self.dispatch(n) for n in notifications}

    def stats(self) -> dict:
        return {
            "sent": len(self._sent),
            "suppressed": len(self._suppressed),
        }


# TODO: Add per-user channel opt-in: accept a preferences dict[str, list[str]] mapping
#       user_id to their opted-in channels; skip dispatch if user hasn't opted into that channel
# TODO: Add a flush_suppressed() -> list[str] method that re-attempts all suppressed
#       notifications that are now outside the cooldown window, returning successfully sent IDs


if __name__ == "__main__":
    dispatcher = NotificationDispatcher(cooldown_seconds=30.0)
    now = time.time()

    notifications = [
        Notification("N001", "user-1", "email", "order_shipped",  "Your order shipped!", now),
        Notification("N002", "user-1", "email", "order_shipped",  "Duplicate — suppress", now + 1),
        Notification("N003", "user-1", "email", "password_reset", "Reset your password", now + 2),   # different type — should NOT suppress
        Notification("N004", "user-1", "sms",   "order_shipped",  "Order shipped (SMS)",  now + 3),  # different channel
        Notification("N005", "user-2", "email", "promo",          "50% off today!",       now + 4),  # different user
        Notification("N006", "user-1", "push",  "promo",          "Don't miss this deal", now + 5),
    ]

    print("=== dispatch_batch ===")
    results = dispatcher.dispatch_batch(notifications)
    for nid, sent in results.items():
        n = next(x for x in notifications if x.notification_id == nid)
        status = "SENT     " if sent else "SUPPRESSED"
        print(f"  {nid} {status}: {n.user_id} / {n.channel} / {n.message_type}")

    print(f"\n  Expected: N001 sent, N002 suppressed, N003 sent, N004 sent, N005 sent, N006 sent")
    print(f"\n=== Stats ===")
    print(f"  {dispatcher.stats()}")
