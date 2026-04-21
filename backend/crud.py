from sqlalchemy.orm import Session
from sqlalchemy import or_

from models import User, Task
from schemas import TaskCreate, TaskUpdate
from auth import hash_password

def create_user(db: Session, username: str, email: str, password: str) -> User:
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def create_task(db: Session, user_id: int, task_data: TaskCreate) -> Task:
    task = Task(
        user_id=user_id,
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
        due_date=task_data.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def get_tasks(
    db: Session,
    user_id: int,
    status: str | None = None,
    priority: str | None = None,
    search: str | None =None,
) -> list[Task]:
    query = db.query(Task).filter(Task.user_id == user_id)

    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if search:
        query = query.filter(
            or_(
                Task.title.ilike(f"%{search}%"),
                Task.description.ilike(f"%{search}%"),
            )
        )
    
    return query.order_by(Task.updated_at.desc()).all()

def get_task(db: Session, task_id: int, user_id: int) -> Task | None:
    return db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == user_id,
    ).first()

def update_task(db: Session, task: Task, task_data: TaskUpdate) -> Task:
    update_dict = task_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(task, key, value)
    
    db.commit()
    db.refresh(task)
    return task

def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()

def get_task_stats(db: Session, user_id: int) -> dict:
    tasks = db.query(Task).filter(Task.user_id == user_id).all()

    stats = {
        "total": len(tasks),
        "todo": sum(1 for t in tasks if t.status == "todo"),
        "in_progress": sum(1 for t in tasks if t.status == "in_progress"),
        "done": sum(1 for t in tasks if t.status == "done"),
        "high_priority": sum(1 for t in tasks if t.priority == "high"),
    }
    return stats