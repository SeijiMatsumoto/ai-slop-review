# AI-generated PR — review this code
# Description: "Added Redis-backed rate limiting middleware for Flask API endpoints"

import time
import redis
from flask import Flask, request, jsonify, g
from functools import wraps

app = Flask(__name__)

# Redis connection
redis_client = redis.Redis(host="localhost", port=6379, db=0)

# Rate limit configuration
DEFAULT_RATE_LIMIT = 100  # requests
DEFAULT_WINDOW = 60  # seconds


def get_client_ip() -> str:
    """Get the client's IP address."""
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr


def rate_limit(max_requests: int = DEFAULT_RATE_LIMIT, window: int = DEFAULT_WINDOW):
    """Rate limiting decorator for Flask routes."""

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            client_ip = get_client_ip()
            endpoint = request.endpoint
            key = f"rate_limit:{client_ip}:{endpoint}"

            # Get current request count
            current = redis_client.get(key)

            if current is None:
                # First request in this window
                redis_client.set(key, 1, ex=window)
                current_count = 1
            else:
                current_count = int(current)
                if current_count >= max_requests:
                    # Calculate time remaining in window
                    ttl = redis_client.ttl(key)
                    return jsonify({
                        "error": "Rate limit exceeded",
                        "retry_after": ttl,
                        "limit": max_requests,
                        "window": window,
                        "current_usage": current_count,
                    }), 429

                # Increment the counter
                redis_client.incr(key)
                current_count += 1

            # Add rate limit headers to response
            response = f(*args, **kwargs)

            if isinstance(response, tuple):
                resp_obj, status_code = response
            else:
                resp_obj = response
                status_code = 200

            if hasattr(resp_obj, "headers"):
                resp_obj.headers["X-RateLimit-Limit"] = str(max_requests)
                resp_obj.headers["X-RateLimit-Remaining"] = str(
                    max_requests - current_count
                )
                resp_obj.headers["X-RateLimit-Window"] = str(window)
                resp_obj.headers["X-RateLimit-ClientIP"] = client_ip

            return resp_obj, status_code

        return wrapped

    return decorator


@app.route("/api/data", methods=["GET"])
@rate_limit(max_requests=10, window=60)
def get_data():
    """Sample protected endpoint."""
    return jsonify({"data": "Here is your data", "timestamp": time.time()}), 200


@app.route("/api/submit", methods=["POST"])
@rate_limit(max_requests=5, window=60)
def submit_data():
    """Sample rate-limited POST endpoint."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    return jsonify({"status": "accepted", "received": data}), 201


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint — not rate limited."""
    try:
        redis_client.ping()
        redis_status = "connected"
    except redis.ConnectionError:
        redis_status = "disconnected"

    return jsonify({
        "status": "healthy",
        "redis": redis_status,
        "timestamp": time.time(),
    }), 200


@app.route("/api/rate-limit-status", methods=["GET"])
@rate_limit(max_requests=30, window=60)
def rate_limit_status():
    """Check your current rate limit usage."""
    client_ip = get_client_ip()
    keys = redis_client.keys(f"rate_limit:{client_ip}:*")

    usage = {}
    for key in keys:
        endpoint = key.decode().split(":")[-1]
        count = redis_client.get(key)
        ttl = redis_client.ttl(key)
        usage[endpoint] = {
            "current_count": int(count) if count else 0,
            "ttl_seconds": ttl,
        }

    return jsonify({"client_ip": client_ip, "usage": usage}), 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
