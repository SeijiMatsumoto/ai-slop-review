# AI-generated PR — review this code
# Description: Added password reset request and confirmation endpoints

import hashlib
import time
import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = "app.db"
SMTP_HOST = "smtp.example.com"
SMTP_PORT = 587
SMTP_USER = "noreply@example.com"
SMTP_PASS = "smtp-password"
BASE_URL = "https://app.example.com"


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def generate_reset_token(email: str) -> str:
    """Generate a unique reset token for the given email."""
    timestamp = str(int(time.time()))
    raw = email + timestamp
    token = hashlib.md5(raw.encode()).hexdigest()
    return token


def send_reset_email(email: str, token: str):
    """Send the password reset email to the user."""
    reset_link = f"{BASE_URL}/reset-password?token={token}"
    body = f"""
    Hello,

    You requested a password reset. Click the link below to reset your password:

    {reset_link}

    If you didn't request this, please ignore this email.

    Best regards,
    The Team
    """
    msg = MIMEText(body)
    msg["Subject"] = "Password Reset Request"
    msg["From"] = SMTP_USER
    msg["To"] = email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


@app.route("/api/password-reset/request", methods=["POST"])
def request_reset():
    """Handle password reset request — sends a reset email if user exists."""
    data = request.get_json()
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({"error": "Email is required"}), 400

    conn = get_db()
    user = conn.execute(
        "SELECT id, email FROM users WHERE email = ?", (email,)
    ).fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    # Generate token and store it
    token = generate_reset_token(email)
    conn.execute(
        "INSERT INTO password_reset_tokens (user_id, token) VALUES (?, ?)",
        (user["id"], token),
    )
    conn.commit()
    conn.close()

    # Send the reset email
    try:
        send_reset_email(email, token)
    except Exception as e:
        app.logger.error(f"Failed to send reset email: {e}")
        return jsonify({"error": "Failed to send email"}), 500

    return jsonify({"message": "Reset email sent"}), 200


@app.route("/api/password-reset/confirm", methods=["POST"])
def confirm_reset():
    """Handle password reset confirmation — validates token and updates password."""
    data = request.get_json()
    token = data.get("token", "").strip()
    new_password = data.get("password", "")

    if not token or not new_password:
        return jsonify({"error": "Token and password are required"}), 400

    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    conn = get_db()
    reset_record = conn.execute(
        "SELECT user_id, created_at FROM password_reset_tokens WHERE token = ?",
        (token,),
    ).fetchone()

    if not reset_record:
        conn.close()
        return jsonify({"error": "Invalid reset token"}), 400

    # Hash the new password and update the user record
    password_hash = hashlib.md5(new_password.encode()).hexdigest()
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (password_hash, reset_record["user_id"]),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Password updated successfully"}), 200


@app.route("/api/password-reset/validate-token", methods=["GET"])
def validate_token():
    """Check if a reset token is valid (used by the frontend before showing the form)."""
    token = request.args.get("token", "").strip()

    if not token:
        return jsonify({"valid": False}), 400

    conn = get_db()
    reset_record = conn.execute(
        "SELECT user_id, created_at FROM password_reset_tokens WHERE token = ?",
        (token,),
    ).fetchone()
    conn.close()

    if not reset_record:
        return jsonify({"valid": False}), 200

    return jsonify({"valid": True}), 200


if __name__ == "__main__":
    init_db()
    app.run(debug=False, host="0.0.0.0", port=5000)
