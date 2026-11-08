"""Unit tests for the Student Registration Flask API.

Database calls are mocked so these tests do not require or modify MariaDB.
Run from python_app/python with: pytest -v
"""
from unittest.mock import MagicMock

import pymysql
import pytest

from app import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


def make_db_connection(*, fetchone=None, lastrowid=1, execute_error=None):
    """Create a mock PyMySQL connection/cursor context-manager pair."""
    connection = MagicMock()
    cursor = MagicMock()
    connection.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchone.return_value = fetchone
    cursor.lastrowid = lastrowid
    if execute_error is not None:
        cursor.execute.side_effect = execute_error
    return connection, cursor


def test_health_returns_ok_when_database_is_available(client, monkeypatch):
    connection = MagicMock()
    monkeypatch.setattr("app.get_connection", lambda: connection)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "database": "connected"}
    connection.close.assert_called_once()


def test_health_returns_503_when_database_is_unavailable(client, monkeypatch):
    def raise_database_error():
        raise pymysql.MySQLError("database unavailable")

    monkeypatch.setattr("app.get_connection", raise_database_error)

    response = client.get("/api/health")

    assert response.status_code == 503
    assert response.get_json() == {"status": "error", "database": "unavailable"}


def test_create_student_returns_201(client, monkeypatch):
    connection, cursor = make_db_connection(lastrowid=42)
    monkeypatch.setattr("app.get_connection", lambda: connection)

    response = client.post(
        "/api/students",
        json={"reg_no": "STU1001", "name": "Alex", "age": 21},
    )

    assert response.status_code == 201
    assert response.get_json() == {"message": "Student registered", "id": 42}
    cursor.execute.assert_called_once_with(
        "INSERT INTO students (reg_no, name, age) VALUES (%s, %s, %s)",
        ("STU1001", "Alex", 21),
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"reg_no": "STU1001", "age": 21},
        {"reg_no": "STU1001", "name": "Alex"},
    ],
)
def test_create_student_rejects_missing_fields(client, payload):
    response = client.post("/api/students", json=payload)

    assert response.status_code == 400
    assert response.get_json()["error"] == "reg_no, name, and age are required"


@pytest.mark.parametrize("age", [0, 121, "not-a-number"])
def test_create_student_rejects_invalid_age(client, age):
    response = client.post(
        "/api/students",
        json={"reg_no": "STU1001", "name": "Alex", "age": age},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "age must be between 1 and 120"


def test_create_student_rejects_duplicate_registration_number(client, monkeypatch):
    duplicate_error = pymysql.err.IntegrityError(1062, "Duplicate entry")
    connection, _ = make_db_connection(execute_error=duplicate_error)
    monkeypatch.setattr("app.get_connection", lambda: connection)

    response = client.post(
        "/api/students",
        json={"reg_no": "STU1001", "name": "Alex", "age": 21},
    )

    assert response.status_code == 409
    assert response.get_json()["error"] == "Registration number already exists"


def test_search_student_returns_student(client, monkeypatch):
    student = {
        "id": 42,
        "reg_no": "STU1001",
        "name": "Alex",
        "age": 21,
        "created_at": "2026-01-01 10:00:00",
    }
    connection, cursor = make_db_connection(fetchone=student)
    monkeypatch.setattr("app.get_connection", lambda: connection)

    response = client.get("/api/students?reg_no=STU1001")

    assert response.status_code == 200
    assert response.get_json() == student
    cursor.execute.assert_called_once()


def test_search_student_requires_registration_number(client):
    response = client.get("/api/students")

    assert response.status_code == 400
    assert response.get_json()["error"] == "Provide a reg_no query parameter"


def test_search_student_returns_404_when_not_found(client, monkeypatch):
    connection, _ = make_db_connection(fetchone=None)
    monkeypatch.setattr("app.get_connection", lambda: connection)

    response = client.get("/api/students?reg_no=UNKNOWN")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Student not found"
