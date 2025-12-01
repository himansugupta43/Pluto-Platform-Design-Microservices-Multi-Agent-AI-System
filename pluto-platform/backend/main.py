import shutil
import os
import uuid
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Form
from starlette.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List
from jose import JWTError, jwt
from pydantic import EmailStr

from app import auth, crud, models, schemas
from app.database import engine, get_db, SessionLocal
from src.model_langchain import HTPModel
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

from loguru import logger  # <--- IMPORT LOGURU
import sys 

logger.remove() 
# Add a new handler that formats and colors the output to the console (stderr)
logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

load_dotenv()
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files for Uploads
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Initialize AI Model
text_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2, google_api_key=os.getenv("GOOGLE_API_KEY"))
htp_model = HTPModel(text_model=text_model, multimodal_model=text_model, use_cache=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

# Dependency for getting current user
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

# Background AI Task
def run_ai_analysis(drawing_id: str, image_path: str):
    db = SessionLocal()
    try:
        logger.info(f"Starting AI analysis for drawing_id: {drawing_id}")
        analysis_result = htp_model.pluto_workflow(image_path=image_path, language="en")
        crud.create_ai_analysis(db, drawing_id=drawing_id, analysis_data=analysis_result)
        crud.update_drawing_status(db, drawing_id, "in_review")
        logger.success(f"AI Analysis COMPLETED for drawing_id: {drawing_id}")
    except Exception as e:
        crud.update_drawing_status(db, drawing_id, "failed")
        logger.error(f"AI Analysis FAILED for drawing_id {drawing_id}: {e}")
    finally:
        db.close()

# --- API Endpoints ---

# AUTH
@app.post("/api/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED, tags=["Auth"])
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/api/token", response_model=schemas.Token, status_code=status.HTTP_200_OK, tags=["Auth"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@app.get("/api/users/me", response_model=schemas.User, status_code=status.HTTP_200_OK, tags=["Users"])
async def read_users_me(current_user: schemas.User = Depends(get_current_user)):
    return current_user

# STUDENT
@app.post("/api/drawings/upload", response_model=schemas.Assessment, status_code=status.HTTP_201_CREATED, tags=["Student"])
async def upload_drawing(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.RoleEnum.student:
        raise HTTPException(status_code=403, detail="Only students can upload drawings.")
    
    # Use a unique filename to prevent overwrites
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join("uploads", unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    drawing = crud.create_drawing(db=db, student_id=current_user.id, file_path=file_path)
    return drawing

@app.get("/api/my-submissions", response_model=List[schemas.Assessment], status_code=status.HTTP_200_OK, tags=["Student"])
def get_my_submissions(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.RoleEnum.student:
        raise HTTPException(status_code=403, detail="Not a student.")
    return crud.get_assessments_for_student(db, student_id=current_user.id)

# FACILITATOR
@app.get("/api/assessments/facilitator", response_model=List[schemas.Assessment], status_code=status.HTTP_200_OK, tags=["Facilitator"])
def get_facilitator_assessments(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.RoleEnum.facilitator:
        raise HTTPException(status_code=403, detail="Not a facilitator.")
    return crud.get_assessments_for_facilitator(db)

@app.get("/api/psychologists", response_model=List[schemas.User], status_code=status.HTTP_200_OK, tags=["Facilitator"])
def list_psychologists(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.RoleEnum.facilitator:
        raise HTTPException(status_code=403, detail="Not a facilitator.")
    return crud.get_psychologists(db)

@app.put("/api/drawings/{drawing_id}/assign/{psychologist_id}", response_model=schemas.Assessment, status_code=status.HTTP_200_OK, tags=["Facilitator"])
def assign_drawing(drawing_id: uuid.UUID, psychologist_id: uuid.UUID, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.RoleEnum.facilitator:
        raise HTTPException(status_code=403, detail="Not a facilitator.")
    
    updated_drawing = crud.assign_drawing(db, drawing_id=drawing_id, psychologist_id=psychologist_id)
    if not updated_drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")

    # This is the new trigger for the AI analysis
    background_tasks.add_task(run_ai_analysis, drawing_id=str(updated_drawing.id), image_path=updated_drawing.file_path)
    
    # Reload from db to get relationships
    return db.query(models.Drawing).filter(models.Drawing.id == drawing_id).first()


# PSYCHOLOGIST
@app.get("/api/assessments/psychologist", response_model=List[schemas.Assessment], status_code=status.HTTP_200_OK, tags=["Psychologist"])
def get_psychologist_assessments(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.RoleEnum.psychologist:
        raise HTTPException(status_code=403, detail="Not a psychologist.")
    return crud.get_assessments_for_psychologist(db, psychologist_id=current_user.id)

@app.post("/api/drawings/{drawing_id}/evaluate", status_code=status.HTTP_200_OK, tags=["Psychologist"])
def save_evaluation(drawing_id: uuid.UUID, evaluation: schemas.EvaluationCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.RoleEnum.psychologist:
        raise HTTPException(status_code=403, detail="Not a psychologist.")

    eval_result = crud.create_or_update_evaluation(db, drawing_id=drawing_id, psychologist_id=current_user.id, notes=evaluation.notes)
    return eval_result

# Database Seeding on Startup (for development)
@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    users_to_create = [
        {"email": "harshit@gmail.com", "password": "password", "role": "student"},
        {"email": "soham@gmail.com", "password": "password", "role": "student"},
        {"email": "ananth@gmail.com", "password": "password", "role": "facilitator"},
        {"email": "ramesh@gmail.com", "password": "password", "role": "psychologist"},
        {"email": "prakash@gmail.com", "password": "password", "role": "psychologist"},
    ]
    for user_data in users_to_create:
        if not crud.get_user_by_email(db, email=user_data["email"]):
            crud.create_user(db, user=schemas.UserCreate(**user_data))
            logger.success(f"Created user: {user_data['email']}")
    db.close()