from sqlalchemy.orm import Session, joinedload
from . import models, schemas, auth
import uuid

# User CRUD
def get_user(db: Session, user_id: uuid.UUID):
    return db.query(models.User).filter(models.User.id == user_id).first()
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()
def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()
def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
def get_psychologists(db: Session):
    return db.query(models.User).filter(models.User.role == 'psychologist').all()

# Drawing / Assessment CRUD
def get_assessments_for_facilitator(db: Session):
    return db.query(models.Drawing).options(
        joinedload(models.Drawing.student),
        joinedload(models.Drawing.psychologist),
    ).order_by(models.Drawing.submitted_at.desc()).all()

def get_assessments_for_psychologist(db: Session, psychologist_id: uuid.UUID):
    return db.query(models.Drawing).filter(models.Drawing.psychologist_id == psychologist_id).options(
        joinedload(models.Drawing.student),
        joinedload(models.Drawing.ai_analysis),
    ).order_by(models.Drawing.submitted_at.desc()).all()

def get_assessments_for_student(db: Session, student_id: uuid.UUID):
    return db.query(models.Drawing).filter(models.Drawing.student_id == student_id).options(
        joinedload(models.Drawing.evaluation)
    ).order_by(models.Drawing.submitted_at.desc()).all()

def create_drawing(db: Session, student_id: uuid.UUID, file_path: str):
    db_drawing = models.Drawing(student_id=student_id, file_path=file_path, status="submitted")
    db.add(db_drawing)
    db.commit()
    db.refresh(db_drawing)
    return db_drawing

def update_drawing_status(db: Session, drawing_id: uuid.UUID, status: str):
    db_drawing = db.query(models.Drawing).filter(models.Drawing.id == drawing_id).first()
    if db_drawing:
        db_drawing.status = status
        db.commit()
        db.refresh(db_drawing)
    return db_drawing

def assign_drawing(db: Session, drawing_id: uuid.UUID, psychologist_id: uuid.UUID):
    db_drawing = db.query(models.Drawing).filter(models.Drawing.id == drawing_id).first()
    if db_drawing:
        db_drawing.psychologist_id = psychologist_id
        db_drawing.status = "processing"
        db.commit()
        db.refresh(db_drawing)
    return db_drawing

# AI Analysis CRUD
def create_ai_analysis(db: Session, drawing_id: uuid.UUID, analysis_data: dict):
    db_analysis = models.AIAnalysis(drawing_id=drawing_id, analysis_data=analysis_data)
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis

# Evaluation CRUD
def create_or_update_evaluation(db: Session, drawing_id: uuid.UUID, psychologist_id: uuid.UUID, notes: str):
    db_eval = db.query(models.Evaluation).filter(models.Evaluation.drawing_id == drawing_id).first()
    if db_eval:
        db_eval.notes = notes
    else:
        db_eval = models.Evaluation(drawing_id=drawing_id, psychologist_id=psychologist_id, notes=notes)
        db.add(db_eval)
    
    update_drawing_status(db, drawing_id, "reviewed")
    db.commit()
    db.refresh(db_eval)
    return db_eval