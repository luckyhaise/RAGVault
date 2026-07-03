from uuid import uuid4, UUID as UUID_PY , uuid1
from sqlalchemy import String , UUID , VARCHAR , Text,Integer,literal ,UniqueConstraint 
from datetime import datetime , UTC
from sqlalchemy import DateTime , ForeignKey , Enum 
from sqlalchemy_utils import EmailType 
from typing import Literal
from sqlalchemy.orm import DeclarativeBase , mapped_column, Mapped, relationship 

class Base(DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = "users"
    id: Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid4)
    name: Mapped[str] = mapped_column(VARCHAR(100),nullable=False)
    password : Mapped[str] = mapped_column(Text,nullable=False)
    phone: Mapped[str] = mapped_column(VARCHAR(20),nullable=False,unique=True)
    email : Mapped[str] = mapped_column(EmailType,unique=True,nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default= lambda: datetime.now(UTC)) 
    updated_at : Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(UTC),onupdate=lambda:datetime.now(UTC))
    deleted_at : Mapped[datetime|None] = mapped_column(DateTime(timezone=True),default=None,nullable=True)
    documents = relationship("Documents",back_populates="user",cascade="all, delete-orphan")
    llm_runs = relationship("Llm_Runs",back_populates="user",cascade="all, delete-orphan")
    ingestion_jobs = relationship("Ingestion_Jobs",back_populates="user",cascade="all, delete-orphan") 
    __table_args__ =  (UniqueConstraint("phone","email" ,name="uq_phone_email"),)
class Documents(Base):
    __tablename__ = "documents"

    id : Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid4)
    user_id: Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(VARCHAR(100),nullable=False)
    original_text: Mapped[str] = mapped_column(Text,nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default= lambda:datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default= lambda: datetime.now(UTC),onupdate=lambda: datetime.now(UTC))
    deleted_at : Mapped[datetime|None] = mapped_column(DateTime(timezone=True),default=None,nullable=True)
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
    document_id: Mapped[UUID_PY] = mapped_column(UUID(as_uuid=True),ForeignKey("documents.id",ondelete="CASCADE"))
    status: Mapped[Literal["pending","completed","failed","processing"]] = mapped_column(Enum("pending","completed","failed","processing",name= "ingestion_jobs_status"),default="pending")
    error_message : Mapped[str|None] = mapped_column(Text,nullable=True,default=None)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)
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