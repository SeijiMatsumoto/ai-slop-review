# Review this code — find bugs, understand the logic, complete the TODOs

import time
import uuid


class SessionManager:
    def __init__(self, ttl_seconds: int = 3600) -> None:
        self.ttl_seconds = ttl_seconds
        self.sessions: dict[str, dict] = {}  # session_id -> session data

    def create(self, user_id: str, metadata: dict | None = None) -> str:
        session_id = str(uuid.uuid4())
        now = time.monotonic()
        self.sessions[session_id] = {
            "user_id": user_id,
            "created_at": now,
            "expires_at": now + self.ttl_seconds,
            "metadata": metadata or {},
        }
        return session_id

    def is_valid(self, session_id: str) -> bool:
        session = self.sessions.get(session_id)
        if session is None:
            return False
        return session["expires_at"] < time.monotonic()

    def get_user(self, session_id: str) -> str | None:
        if not self.is_valid(session_id):
            return None
        return self.sessions[session_id]["user_id"]

    def logout(self, session_id: str) -> bool:
        session = self.sessions.get(session_id)
        if session is None:
            return False
        del self.sessions[session["user_id"]]
        return True

    def active_sessions(self, user_id: str) -> list[str]:
        now = time.monotonic()
        return [
            sid for sid, s in self.sessions.items()
            if s["user_id"] == user_id and s["expires_at"] > now
        ]

    def purge_expired(self) -> int:
        now = time.monotonic()
        expired = [sid for sid, s in self.sessions.items() if s["expires_at"] <= now]
        for sid in expired:
            del self.sessions[sid]
        return len(expired)


# TODO: Add a refresh(session_id: str, extend_by: int | None = None) -> bool method
#       that resets expires_at to now + ttl_seconds (or now + extend_by if provided);
#       return False if session doesn't exist or is already expired
# TODO: Enforce a max_sessions_per_user limit in create() — if the user already has that
#       many active sessions, evict the oldest one (by created_at) before creating the new one


if __name__ == "__main__":
    mgr = SessionManager(ttl_seconds=10)

    print("=== Create sessions ===")
    s1 = mgr.create("user-1", metadata={"ip": "192.168.1.1"})
    s2 = mgr.create("user-1", metadata={"ip": "192.168.1.2"})
    s3 = mgr.create("user-2", metadata={"ip": "10.0.0.1"})
    print(f"  s1={s1[:8]}..., s2={s2[:8]}..., s3={s3[:8]}...")

    print("\n=== is_valid ===")
    print(f"  s1 valid: {mgr.is_valid(s1)} (expected True)")
    print(f"  fake valid: {mgr.is_valid('not-a-session')} (expected False)")

    print("\n=== get_user ===")
    print(f"  user for s1: {mgr.get_user(s1)} (expected user-1)")
    print(f"  user for s3: {mgr.get_user(s3)} (expected user-2)")

    print("\n=== active_sessions ===")
    print(f"  user-1 active: {len(mgr.active_sessions('user-1'))} (expected 2)")
    print(f"  user-2 active: {len(mgr.active_sessions('user-2'))} (expected 1)")

    print("\n=== logout ===")
    try:
        result = mgr.logout(s1)
        print(f"  logout s1: {result}")
        print(f"  sessions remaining: {len(mgr.sessions)} (expected 2)")
    except KeyError as e:
        print(f"  logout s1: KeyError {e}")

    print("\n=== purge_expired (sleep 11s) ===")
    time.sleep(11)
    purged = mgr.purge_expired()
    print(f"  purged: {purged}, remaining: {len(mgr.sessions)}")
