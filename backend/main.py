from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, init_db
from models import User
from schemas import (
    UserCreate, UserResponse,
    LoginRequest, TokenResponse,
    TaskCreate, TaskUpdate, TaskResponse,
)
from auth import (
    verify_password,
    create_access_token,
    get_current_user,
)
import crud

app = FastAPI(
    title="Task Manager API",
    description="タスク管理アプリのバックエンド",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/")
def root():
    return {"status": "ok", "message": "Task Manager API is running"}

@app.post("/auth/register", response_model=UserResponse)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_username(db, body.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このユーザー名は既に使われています",
        )

    if crud.get_user_by_email(db, body.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスは既に使われています",
        )
    
    user = crud.create_user(db, body.username, body.email, body.password)
    return user

@app.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, body.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません",
        )

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません",
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return TokenResponse(access_token=access_token)

@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/tasks", response_model=TaskResponse)
def create_task(
    body: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = crud.create_task(db, current_user.id, body)
    return task

@app.get("/tasks", response_model=list[TaskResponse])
def get_tasks(
    status: str | None = None,
    priority: str | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tasks = crud.get_tasks(
        db,
        current_user.id,
        status=status,
        priority=priority,
        search=search,
    )
    return tasks


@app.get("/tasks/stats")
def get_task_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.get_task_stats(db, current_user.id)

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = crud.get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="タスクが見つかりません",
        )
    return task

@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    body: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = crud.get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="タスクが見つかりません",
        )
    updated_task = crud.update_task(db, task, body)
    return updated_task


@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = crud.get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="タスクが見つかりません",
        )
    crud.delete_task(db, task)
    return {"message": "タスクを削除しました"}