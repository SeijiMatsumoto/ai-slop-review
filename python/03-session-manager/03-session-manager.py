# Review this code — find bugs, understand the logic, complete the TODOs

import time
import uuid


class SessionManager:
    def __init__(self, ttl_seconds: int = 3600) -> None:
        self.ttl_seconds = ttl_seconds
        self.sessions: dict[str, dict] = {}  # session_id -> session data 
        self.max_sessions_per_user: int | None = None

    def create(self, user_id: str, metadata: dict | None = None) -> str:
        session_id = str(uuid.uuid4())

        user_sessions = self.get_user_sessions(user_id)
        if self.max_sessions_per_user is not None:
            if len(user_sessions) >= self.max_sessions_per_user:
                del self.sessions[user_sessions[0][0]]

        now = time.monotonic()
        self.sessions[session_id] = {
            "user_id": user_id,
            "created_at": now,
            "expires_at": now + self.ttl_seconds,
            "metadata": metadata or {},
        }
        return session_id
    
    def get_user_sessions(self, user_id: str) -> list[dict[str, dict]]:
        return sorted(
            [ 
                (session_id, session) for session_id, session in self.sessions.items() 
                if session.get("user_id") == user_id and self.is_valid(session_id)
            ],
            key=lambda t: t[1]["created_at"]
        )


    def is_valid(self, session_id: str) -> bool:
        now = time.monotonic()
        session = self.sessions.get(session_id)
        if session is None:
            return False
        return session["expires_at"] > now 

    def get_user(self, session_id: str) -> str | None:
        if not self.is_valid(session_id):
            return None
        return self.sessions[session_id]["user_id"]

    def logout(self, session_id: str) -> bool:
        session = self.sessions.get(session_id)
        if session is None:
            return False
        del self.sessions[session_id]
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


    def refresh(self, session_id: str, extend_by: int | None = None) -> bool:
        session = self.sessions.get(session_id)
        if session is None or not self.is_valid(session_id):
            return False
        if extend_by is None:
            session["expires_at"] = time.monotonic() + self.ttl_seconds
        else:
            session["expires_at"] = time.monotonic() + extend_by
        return True



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

    print("\n=== refresh ===")
    mgr2 = SessionManager(ttl_seconds=5)
    r1 = mgr2.create("user-1")
    before = mgr2.sessions[r1]["expires_at"]
    time.sleep(2)
    mgr2.refresh(r1)
    after = mgr2.sessions[r1]["expires_at"]
    print(f"  expires_at extended: {after > before} (expected True)")
    print(f"  refresh nonexistent: {mgr2.refresh('fake-id')} (expected False)")

    print("\n=== refresh with extend_by ===")
    r2 = mgr2.create("user-2")
    before2 = mgr2.sessions[r2]["expires_at"]
    mgr2.refresh(r2, extend_by=60)
    after2 = mgr2.sessions[r2]["expires_at"]
    print(f"  extended by 60s (not ttl=5s): {after2 - before2:.0f}s gap (expected ~55)")

    print("\n=== refresh on expired session ===")
    mgr3 = SessionManager(ttl_seconds=1)
    r3 = mgr3.create("user-1")
    time.sleep(2)
    print(f"  refresh expired session: {mgr3.refresh(r3)} (expected False)")

    print("\n=== max_sessions_per_user (limit=1) ===")
    mgr4 = SessionManager(ttl_seconds=30)
    mgr4.max_sessions_per_user = 1
    a1 = mgr4.create("user-1")
    print(f"  after 1st create: {len(mgr4.active_sessions('user-1'))} active (expected 1)")
    a2 = mgr4.create("user-1")
    active = mgr4.active_sessions("user-1")
    print(f"  after 2nd create: {len(active)} active (expected 1 — oldest evicted)")
    print(f"  old session still valid: {mgr4.is_valid(a1)} (expected False)")
    print(f"  new session valid: {mgr4.is_valid(a2)} (expected True)")
