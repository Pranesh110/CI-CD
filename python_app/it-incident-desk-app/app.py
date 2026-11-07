import os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from db import engine, get_db
from models import (
    AuditLog, Incident, IncidentPriority, IncidentStatus, User, UserRole
)

JWT_SECRET = os.getenv("JWT_SECRET", "local-development-secret-change-this")
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
password_hash = PasswordHash.recommended()
bearer = HTTPBearer()


# ----- API schemas -----

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    role: UserRole


class IncidentCreate(BaseModel):
    title: str = Field(min_length=4, max_length=200)
    description: str = Field(min_length=5)
    priority: IncidentPriority = IncidentPriority.MEDIUM


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=4, max_length=200)
    description: str | None = Field(default=None, min_length=5)
    priority: IncidentPriority | None = None
    status: IncidentStatus | None = None
    assignee_id: int | None = None


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    priority: IncidentPriority
    status: IncidentStatus
    reporter_id: int
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime


# ----- Authentication -----

def make_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expires}, JWT_SECRET, algorithm="HS256")


def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        user_id = int(payload.get("sub", ""))
    except (jwt.PyJWTError, ValueError, TypeError):
        raise unauthorized

    user = db.get(User, user_id)
    if user is None:
        raise unauthorized
    return user


def allow_roles(*roles: UserRole):
    def checker(user: User = Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker


app = FastAPI(
    title="HelpDesk Pro API",
    description="IT Service Desk and Incident Management API",
    version="1.0.0",
)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy", "service": "helpdesk-api"}


@app.get("/health/db", tags=["Health"])
def database_health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "connected"}


@app.post("/api/auth/register", response_model=UserResponse, status_code=201, tags=["Authentication"])
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="Email already registered")

    # Public signup is restricted to end_user; do not accept a role from the client.
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=password_hash.hash(payload.password),
        role=UserRole.END_USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/auth/login", response_model=TokenResponse, tags=["Authentication"])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not password_hash.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return TokenResponse(access_token=make_token(user.id))


@app.get("/api/auth/me", response_model=UserResponse, tags=["Authentication"])
def get_me(user: User = Depends(current_user)):
    return user


@app.post("/api/incidents", response_model=IncidentResponse, status_code=201, tags=["Incidents"])
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    incident = Incident(**payload.model_dump(), reporter_id=user.id)
    db.add(incident)
    db.flush()
    db.add(AuditLog(
        incident_id=incident.id,
        actor_id=user.id,
        action="created",
        details="Incident created",
    ))
    db.commit()
    db.refresh(incident)
    return incident


@app.get("/api/incidents", response_model=list[IncidentResponse], tags=["Incidents"])
def list_incidents(db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = select(Incident).order_by(Incident.created_at.desc())
    if user.role == UserRole.END_USER:
        query = query.where(Incident.reporter_id == user.id)
    return list(db.scalars(query).all())


@app.get("/api/incidents/{incident_id}", response_model=IncidentResponse, tags=["Incidents"])
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    if user.role == UserRole.END_USER and incident.reporter_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed to view this incident")
    return incident


@app.patch("/api/incidents/{incident_id}", response_model=IncidentResponse, tags=["Incidents"])
def update_incident(
    incident_id: int,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles(UserRole.ADMIN, UserRole.SUPPORT)),
):
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    changes = payload.model_dump(exclude_unset=True)
    if changes.get("assignee_id") is not None:
        assignee = db.get(User, changes["assignee_id"])
        if assignee is None or assignee.role not in (UserRole.ADMIN, UserRole.SUPPORT):
            raise HTTPException(status_code=400, detail="Assignee must be support or admin")

    for field, value in changes.items():
        setattr(incident, field, value)

    db.add(AuditLog(
        incident_id=incident.id,
        actor_id=user.id,
        action="updated",
        details=", ".join(changes.keys()),
    ))
    db.commit()
    db.refresh(incident)
    return incident


@app.delete("/api/incidents/{incident_id}", status_code=204, tags=["Incidents"])
def delete_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(allow_roles(UserRole.ADMIN)),
):
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    db.delete(incident)
    db.commit()
    return None
