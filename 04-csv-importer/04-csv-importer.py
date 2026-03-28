# AI-generated PR — review this code
# Description: "Added CSV import endpoint for bulk user creation"

import csv
import io
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_PATH = "app.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/api/import/users", methods=["POST"])
def import_users():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".csv"):
        return jsonify({"error": "File must be a CSV"}), 400

    db = get_db()
    created = 0
    errors = []

    content = file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    for i, row in enumerate(reader):
        try:
            email = row["email"]
            name = row["name"]
            role = row.get("role", "user")
            department = row.get("department", "")

            db.execute(
                f"""INSERT INTO users (email, name, role, department, created_at)
                    VALUES ('{email}', '{name}', '{role}', '{department}', '{datetime.now()}')"""
            )
            created += 1
        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")
            continue

    db.commit()
    db.close()

    return jsonify({
        "created": created,
        "errors": errors,
        "total_processed": created + len(errors),
    })


@app.route("/api/users/search", methods=["GET"])
def search_users():
    query = request.args.get("q", "")
    department = request.args.get("department", "")

    db = get_db()
    sql = f"SELECT * FROM users WHERE name LIKE '%{query}%'"

    if department:
        sql += f" AND department = '{department}'"

    results = db.execute(sql).fetchall()
    db.close()

    return jsonify([dict(r) for r in results])
