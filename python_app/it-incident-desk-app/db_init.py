"""
One-time database bootstrap:
1. Connect to PostgreSQL's maintenance database.
2. Create DB_NAME if it does not exist.
3. Create application tables.
4. Insert initial admin, support and end-user accounts plus a demo incident.

Run: python db_init.py

Set DB_ADMIN_USER / DB_ADMIN_PASSWORD if the DB_USER account is not allowed
to create databases. Never use the demo passwords in a real environment.
"""
import os
from sqlalchemy import create_engine, text, select
from sqlalchemy.engine import URL
from pwdlib import PasswordHash

from db import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, engine, SessionLocal, Base
from models import User, Incident, AuditLog, UserRole, IncidentPriority, IncidentStatus

password_hash = PasswordHash.recommended()


def create_database_if_missing():
    admin_user = os.getenv("DB_ADMIN_USER", DB_USER)
    admin_password = os.getenv("DB_ADMIN_PASSWORD", DB_PASSWORD)
    maintenance_db = os.getenv("DB_MAINTENANCE_DB", "postgres")

    admin_url = URL.create(
        "postgresql+psycopg",
        username=admin_user,
        password=admin_password,
        host=DB_HOST,
        port=int(DB_PORT),
        database=maintenance_db,
    )
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    try:
        with admin_engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": DB_NAME},
            ).scalar()

            if not exists:
                # DB_NAME is quoted as an identifier. Escape embedded quotes.
                safe_db_name = DB_NAME.replace('"', '""')
                connection.execute(text(f'CREATE DATABASE "{safe_db_name}"'))
                print(f"Created database: {DB_NAME}")
            else:
                print(f"Database already exists: {DB_NAME}")
    finally:
        admin_engine.dispose()


def seed_initial_data():
    with SessionLocal() as session:
        admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@helpdesk.local")
        support_email = os.getenv("SEED_SUPPORT_EMAIL", "support@helpdesk.local")
        user_email = os.getenv("SEED_USER_EMAIL", "user@helpdesk.local")

        admin = session.scalar(select(User).where(User.email == admin_email))
        if admin is None:
            admin = User(
                name="HelpDesk Admin",
                email=admin_email,
                password_hash=password_hash.hash(
                    os.getenv("SEED_ADMIN_PASSWORD", "ChangeThisAdmin123!")
                ),
                role=UserRole.ADMIN,
            )
            session.add(admin)

        support = session.scalar(select(User).where(User.email == support_email))
        if support is None:
            support = User(
                name="Support Engineer",
                email=support_email,
                password_hash=password_hash.hash(
                    os.getenv("SEED_SUPPORT_PASSWORD", "ChangeThisSupport123!")
                ),
                role=UserRole.SUPPORT,
            )
            session.add(support)

        end_user = session.scalar(select(User).where(User.email == user_email))
        if end_user is None:
            end_user = User(
                name="Demo Employee",
                email=user_email,
                password_hash=password_hash.hash(
                    os.getenv("SEED_USER_PASSWORD", "ChangeThisUser123!")
                ),
                role=UserRole.END_USER,
            )
            session.add(end_user)

        session.flush()

        existing_incident = session.scalar(
            select(Incident).where(Incident.title == "VPN connection unavailable")
        )
        if existing_incident is None:
            incident = Incident(
                title="VPN connection unavailable",
                description="Unable to connect to the corporate VPN from the office network.",
                priority=IncidentPriority.HIGH,
                status=IncidentStatus.OPEN,
                reporter_id=end_user.id,
                assignee_id=support.id,
            )
            session.add(incident)
            session.flush()
            session.add(
                AuditLog(
                    incident_id=incident.id,
                    actor_id=admin.id,
                    action="created",
                    details="Initial demo incident created by database initializer",
                )
            )

        session.commit()
        print("Initial users and demo incident are ready.")


if __name__ == "__main__":
    create_database_if_missing()
    # Importing models above registers all tables with Base metadata.
    Base.metadata.create_all(bind=engine)
    print("Application tables created/verified.")
    seed_initial_data()
    print("Database initialization completed.")
