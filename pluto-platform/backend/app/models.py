# backend/app/models.py
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum as SQLAlchemyEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import datetime
import enum
from .database import Base

class RoleEnum(str, enum.Enum):
    student = "student"
    facilitator = "facilitator"
    psychologist = "psychologist"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLAlchemyEnum(RoleEnum), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    drawings = relationship("Drawing", foreign_keys="[Drawing.student_id]", back_populates="student")

class Drawing(Base):
    __tablename__ = "drawings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    psychologist_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    file_path = Column(String, nullable=False)
    status = Column(String, default="submitted") # submitted -> processing -> in_review -> reviewed
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    student = relationship("User", foreign_keys=[student_id], back_populates="drawings")
    psychologist = relationship("User", foreign_keys=[psychologist_id])
    ai_analysis = relationship("AIAnalysis", back_populates="drawing", uselist=False, cascade="all, delete-orphan")
    evaluation = relationship("Evaluation", back_populates="drawing", uselist=False, cascade="all, delete-orphan")

class AIAnalysis(Base):
    __tablename__ = "ai_analysis"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drawing_id = Column(UUID(as_uuid=True), ForeignKey("drawings.id"), unique=True)
    analysis_data = Column(JSONB)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    drawing = relationship("Drawing", back_populates="ai_analysis")

class Evaluation(Base):
    __tablename__ = "evaluations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drawing_id = Column(UUID(as_uuid=True), ForeignKey("drawings.id"), unique=True)
    psychologist_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    drawing = relationship("Drawing", back_populates="evaluation")