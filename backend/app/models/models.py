from datetime import UTC, datetime
from typing import Literal
from uuid import UUID as UUID_PY
from uuid import uuid4

from sqlalchemy import (
    UUID,
    VARCHAR,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy_utils import EmailType


class Base(DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = "users"
    id: Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid4)
    user_name : Mapped[str] = mapped_column(VARCHAR(200),nullable=False)
    name: Mapped[str] = mapped_column(VARCHAR(100),nullable=False)
    password : Mapped[str] = mapped_column(Text,nullable=False)
    phone: Mapped[str] = mapped_column(VARCHAR(20),nullable=False)
    email : Mapped[str] = mapped_column(EmailType,nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default= lambda: datetime.now(UTC)) 
    updated_at : Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(UTC),onupdate=lambda:datetime.now(UTC))
    documents = relationship("Documents",back_populates="user",cascade="all, delete-orphan")
    llm_runs = relationship("Llm_Runs",back_populates="user",cascade="all, delete-orphan")
    ingestion_jobs = relationship("Ingestion_Jobs",back_populates="user",cascade="all, delete-orphan") 
    sessions = relationship("UserSession",back_populates="user")
    __table_args__ = (
        UniqueConstraint("phone", name="uq_phone"),
        UniqueConstraint("email", name="uq_email"),
        UniqueConstraint("user_name", name="uq_user_name"),
    )
class Documents(Base):
    __tablename__ = "documents"

    id : Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid4)
    user_id: Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(VARCHAR(100),nullable=False)
    original_text: Mapped[str] = mapped_column(Text,nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default= lambda:datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default= lambda: datetime.now(UTC),onupdate=lambda: datetime.now(UTC))
    user = relationship("Users",back_populates="documents")
    chunks = relationship("Documents_Chunks",order_by=lambda:Documents_Chunks.chunk_index.asc(),back_populates="document",cascade="all, delete-orphan")
    ingestion_jobs= relationship("Ingestion_Jobs",back_populates="document",cascade="all, delete-orphan")
    llm_runs = relationship("Llm_Runs",back_populates="document",cascade="all, delete-orphan")


class Documents_Chunks(Base):
    __tablename__ = "document_chunks"
    document_id:Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True),ForeignKey("documents.id",ondelete="CASCADE"),primary_key=True) 
    chunk_index: Mapped[int] = mapped_column(Integer,primary_key=True)
    content: Mapped[str] = mapped_column(Text,nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda:datetime.now(UTC))
    document = relationship(
        "Documents",
        back_populates="chunks"
    )
class Ingestion_Jobs(Base):
    __tablename__ = "ingestion_jobs"
    id: Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True),default=uuid4,primary_key=True)
    user_id : Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE"))
    document_id: Mapped[UUID_PY|None] = mapped_column(UUID(as_uuid=True),ForeignKey("documents.id",ondelete="SET NULL"),nullable=True)
    status: Mapped[Literal["pending","completed","failed","processing"]] = mapped_column(Enum("pending","completed","failed","processing",name= "ingestion_jobs_status"),default="pending")
    error_message : Mapped[str|None] = mapped_column(Text,nullable=True,default=None)
    idempotency_key: Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True),nullable=False,default=uuid4)
    updated_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=lambda : datetime.now(UTC),default=lambda:datetime.now(UTC))
    completed_at : Mapped[datetime|None] = mapped_column(DateTime(timezone=True),default=None,nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default= lambda:datetime.now(UTC))
    document = relationship("Documents",back_populates="ingestion_jobs")
    user = relationship("Users",back_populates="ingestion_jobs")
    
    __table_args__ = (
    UniqueConstraint(
        "user_id",
        "idempotency_key",
        name="uq_document_idempotency_key"
    ),)


    
class Llm_Runs(Base):
    __tablename__ = "llm_runs"
    id: Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True),default=uuid4,primary_key=True)
    user_id : Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE"))
    document_id: Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True),ForeignKey("documents.id",ondelete="CASCADE"))
    model: Mapped[str] = mapped_column(VARCHAR(100))
    prompt: Mapped[str] = mapped_column(Text)
    response: Mapped[str|None] = mapped_column(Text,default=None,nullable=True)
    status: Mapped[Literal["pending","completed","failed","processing"]] = mapped_column(Enum("pending","completed","failed","processing",name="llm_runs_status"),default="pending")
    latency_ms:Mapped[int|None] = mapped_column(Integer,default=None,nullable=True)
    error_message:Mapped[str|None] = mapped_column(Text,default=None,nullable=True)
    started_at : Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(UTC))
    completed_at : Mapped[datetime|None] = mapped_column(DateTime(timezone=True),nullable=True) 
    document = relationship("Documents",back_populates="llm_runs")
    user = relationship("Users",back_populates="llm_runs")

class EmailVerificationOtp(Base):
    __tablename__ = "email_verification_otp"
    id: Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True),default=uuid4,primary_key=True)
    email : Mapped[str] = mapped_column(EmailType,nullable=False)
    otp_hash: Mapped[str] = mapped_column(Text,nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
class UserSession(Base):
    __tablename__ = "user_sessions"
    id: Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    refresh_token_jti:Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True),nullable=False,unique=True,index=True)
    is_revoked:Mapped[bool] = mapped_column(Boolean,default=False,nullable=False)
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False,default=lambda:datetime.now(UTC))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user = relationship("Users",back_populates="sessions")
