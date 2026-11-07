# HelpDesk Pro - separated application and database setup

Files:
- `app.py`: FastAPI routes and API logic.
- `db.py`: PostgreSQL connection/session.
- `models.py`: SQLAlchemy table definitions.
- `db_init.py`: creates the PostgreSQL database (if missing), creates tables, and inserts seed users/demo incident.
- `database/Dockerfile`: PostgreSQL image definition.

## Run locally
1. Start PostgreSQL and create a login role if needed, or use an account that can create databases.
2. Copy `.env.example` to `.env` and export its variables into your shell (or use `set -a; source .env; set +a` in Bash).
3. Install: `pip install -r requirements.txt`
4. Initialize: `python db_init.py`
5. Start API: `uvicorn app:app --reload`
6. Open `http://localhost:8000/docs`.

For local development, `DB_ADMIN_USER` must have permission to create databases. In containerized deployment, the PostgreSQL container's `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` can create the database on first initialization; in that case, set DB_NAME/DB_USER/DB_PASSWORD to those values and db_init.py only needs permission to connect and create tables. Do not give the application a superuser account in production.

The seed accounts are demo credentials. Change every seed password before running, and never expose seeded admin credentials in a public environment. Use a secret manager for deployed secrets.

This starter uses SQLAlchemy `create_all` for initial schema creation. Use Alembic migrations for ongoing schema changes in Dev/Production.
