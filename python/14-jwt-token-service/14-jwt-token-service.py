# AI-generated PR — review this code
# Description: "Added JWT token service with access/refresh token support and blacklisting"

import jwt
import time
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuration
SECRET_KEY = "jwt-secret-2024"
ACCESS_TOKEN_EXPIRY = 15  # minutes
REFRESH_TOKEN_EXPIRY = 30  # days

# In-memory stores
users_db = {
    "alice": {"password": "hashed_pw_1", "role": "admin"},
    "bob": {"password": "hashed_pw_2", "role": "user"},
}
token_blacklist = set()
refresh_tokens = {}


def create_access_token(username: str, role: str) -> str:
    """Generate a short-lived access token."""
    payload = {
        "sub": username,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(seconds=ACCESS_TOKEN_EXPIRY),
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, SECRET_KEY)
    return token


def create_refresh_token(username: str) -> str:
    """Generate a long-lived refresh token."""
    token_id = str(uuid.uuid4())
    refresh_tokens[token_id] = {
        "username": username,
        "created_at": time.time(),
    }
    token = jwt.encode(
        {"sub": username, "jti": token_id, "type": "refresh"},
        SECRET_KEY,
    )
    return token


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256", "none"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def is_token_blacklisted(token: str) -> bool:
    """Check if a token has been revoked."""
    return token in token_blacklist


@app.route("/auth/login", methods=["POST"])
def login():
    """Authenticate user and return access + refresh tokens."""
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = users_db.get(username)
    if not user or user["password"] != password:
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(username, user["role"])
    refresh_token = create_refresh_token(username)

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": ACCESS_TOKEN_EXPIRY,
    }), 200


@app.route("/auth/refresh", methods=["POST"])
def refresh():
    """Issue a new access token using a refresh token."""
    data = request.get_json()
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return jsonify({"error": "Refresh token required"}), 400

    payload = verify_token(refresh_token)
    if not payload:
        return jsonify({"error": "Invalid refresh token"}), 401

    token_id = payload.get("jti")
    token_data = refresh_tokens.get(token_id)

    if not token_data:
        return jsonify({"error": "Refresh token not found"}), 401

    username = token_data["username"]
    user = users_db.get(username)

    if not user:
        return jsonify({"error": "User no longer exists"}), 401

    new_access_token = create_access_token(username, user["role"])

    return jsonify({
        "access_token": new_access_token,
        "expires_in": ACCESS_TOKEN_EXPIRY,
    }), 200


@app.route("/auth/logout", methods=["POST"])
def logout():
    """Revoke the current access token."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing token"}), 401

    token = auth_header.split(" ")[1]
    token_blacklist.add(token)

    return jsonify({"message": "Logged out successfully"}), 200


@app.route("/protected", methods=["GET"])
def protected_resource():
    """A protected endpoint that requires a valid access token."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing token"}), 401

    token = auth_header.split(" ")[1]

    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "Invalid or expired token"}), 401

    if is_token_blacklisted(token):
        return jsonify({"error": "Token has been revoked"}), 401

    return jsonify({
        "message": f"Hello {payload['sub']}",
        "role": payload["role"],
    }), 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
