import os
import time

import pymysql
from flask import Flask, jsonify, request

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "student_user"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "student_db"),
    "cursorclass": pymysql.cursors.DictCursor,
    "connect_timeout": 5,
    "charset": "utf8mb4",
    "autocommit": True,
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def wait_for_database(max_attempts=30, delay=2):
    for attempt in range(1, max_attempts + 1):
        try:
            connection = get_connection()
            connection.close()
            print("Database connection established.")
            return
        except pymysql.MySQLError as exc:
            print(f"Database not ready ({attempt}/{max_attempts}): {exc}")
            time.sleep(delay)

    raise RuntimeError("Could not connect to MariaDB after repeated attempts.")


@app.get("/api/health")
def health():
    try:
        connection = get_connection()
        connection.close()
        return jsonify(status="ok", database="connected"), 200
    except pymysql.MySQLError:
        return jsonify(status="error", database="unavailable"), 503


@app.post("/api/students")
def create_student():
    data = request.get_json(silent=True) or {}
    reg_no = str(data.get("reg_no", "")).strip()
    name = str(data.get("name", "")).strip()
    age = data.get("age")

    if not reg_no or not name or age in (None, ""):
        return jsonify(error="reg_no, name, and age are required"), 400

    try:
        age = int(age)
        if age < 1 or age > 120:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify(error="age must be between 1 and 120"), 400

    try:
        with get_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO students (reg_no, name, age) VALUES (%s, %s, %s)",
                (reg_no, name, age),
            )
            student_id = cursor.lastrowid

        return jsonify(message="Student registered", id=student_id), 201

    except pymysql.err.IntegrityError:
        return jsonify(error="Registration number already exists"), 409

    except pymysql.MySQLError:
        app.logger.exception("Database insert failed")
        return jsonify(error="Database operation failed"), 500


@app.get("/api/students")
def search_student():
    reg_no = request.args.get("reg_no", "").strip()

    if not reg_no:
        return jsonify(error="Provide a reg_no query parameter"), 400

    try:
        with get_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, reg_no, name, age, created_at "
                "FROM students WHERE reg_no = %s",
                (reg_no,),
            )
            student = cursor.fetchone()

        if not student:
            return jsonify(error="Student not found"), 404

        return jsonify(student), 200

    except pymysql.MySQLError:
        app.logger.exception("Database search failed")
        return jsonify(error="Database operation failed"), 500


if __name__ == "__main__":
    wait_for_database()

    # Intentional: required for access from NGINX through the Docker network.
    app.run(host="0.0.0.0", port=8000)  # nosec B104