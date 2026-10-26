from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, Text, ForeignKey, JSON, UniqueConstraint, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc)


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[str] = mapped_column(String(30), primary_key=True)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(ForeignKey("roles.id"))
    department: Mapped[str] = mapped_column(ForeignKey("departments.id"))
    manager_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class Application(Base):
    __tablename__ = "applications"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    levels: Mapped[list] = mapped_column(JSON)


class Policy(Base):
    __tablename__ = "policies"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uid)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), unique=True)
    title: Mapped[str] = mapped_column(String(180))
    department: Mapped[str] = mapped_column(String(80))


class PolicyVersion(Base):
    __tablename__ = "policy_versions"
    __table_args__ = (UniqueConstraint("policy_id", "version"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uid)
    policy_id: Mapped[str] = mapped_column(ForeignKey("policies.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    chunks: Mapped[list] = mapped_column(JSON)
    digest: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AccessRequest(Base):
    __tablename__ = "requests"
    __table_args__ = (UniqueConstraint("requester_id", "idempotency_key"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uid)
    requester_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"))
    justification: Mapped[str] = mapped_column(Text)
    access_level: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(40), index=True, default="submitted")
    revision: Mapped[int] = mapped_column(Integer, default=1)
    idempotency_key: Mapped[str] = mapped_column(String(100))
    payload_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    __mapper_args__ = {"version_id_col": revision}


class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uid)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), index=True)
    result: Mapped[dict] = mapped_column(JSON)
    provider: Mapped[str] = mapped_column(String(40))
    trace_id: Mapped[str] = mapped_column(String(80))
    latency_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Evidence(Base):
    __tablename__ = "evidence"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uid)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"), index=True)
    policy_version_id: Mapped[str] = mapped_column(ForeignKey("policy_versions.id"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    quote: Mapped[str] = mapped_column(Text)


class Decision(Base):
    __tablename__ = "approval_decisions"
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), primary_key=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Fulfilment(Base):
    __tablename__ = "fulfilment_tasks"
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), primary_key=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    reference: Mapped[str | None] = mapped_column(String(200), nullable=True)


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uid)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=uid)
    request_id: Mapped[str | None] = mapped_column(
        ForeignKey("requests.id"), nullable=True, index=True
    )
    actor_id: Mapped[str] = mapped_column(String(80), index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    detail: Mapped[dict] = mapped_column(JSON)
    correlation_id: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class IntegrationEvent(Base):
    __tablename__ = "integration_events"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    kind: Mapped[str] = mapped_column(String(40))
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"))
    digest: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Workflow(Base):
    __tablename__ = "workflow_executions"
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), primary_key=True)
    status: Mapped[str] = mapped_column(String(40))
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
