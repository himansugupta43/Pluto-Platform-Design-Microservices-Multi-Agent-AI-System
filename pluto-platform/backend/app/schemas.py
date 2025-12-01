# backend/app/schemas.py
from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime
from typing import Optional, Any
from .models import RoleEnum

# Base Schemas
class UserBase(BaseModel):
    email: EmailStr
class UserCreate(UserBase):
    password: str
    role: RoleEnum

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: "User"
class TokenData(BaseModel):
    email: Optional[str] = None

# Evaluation Schemas
class EvaluationCreate(BaseModel):
    notes: str
class Evaluation(BaseModel):
    notes: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# AI Analysis Schema
class AIAnalysis(BaseModel):
    analysis_data: Optional[dict]
    class Config:
        from_attributes = True

# User Response Schemas
class User(UserBase):
    id: uuid.UUID
    role: RoleEnum
    class Config:
        from_attributes = True

# Drawing/Assessment Response Schema
class Assessment(BaseModel):
    id: uuid.UUID
    file_path: str
    status: str
    submitted_at: datetime
    student: User
    psychologist: Optional[User] = None
    ai_analysis: Optional[AIAnalysis] = None
    evaluation: Optional[Evaluation] = None
    class Config:
        from_attributes = True
        
Token.update_forward_refs()


        