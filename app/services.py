from typing import List, Optional

from sqlalchemy.orm import Session

from app import models, schemas


def create_task(db: Session, task_in: schemas.TaskCreate) -> models.Task:
    status = task_in.status or "created"
    if status not in ("created", "in_progress", "completed"):
        raise ValueError(f"Invalid status: {status}")

    db_task = models.Task(
        title=task_in.title,
        description=task_in.description or "",
        status=status,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_task(db: Session, task_id: str) -> Optional[models.Task]:
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def get_tasks(db: Session, skip: int = 0, limit: int = 100) -> List[models.Task]:
    return db.query(models.Task).offset(skip).limit(limit).all()


def update_task(db: Session, task_id: str, task_in: schemas.TaskUpdate) -> Optional[models.Task]:
    task = get_task(db, task_id)
    if not task:
        return None

    if task_in.title is not None:
        task.title = task_in.title
    if task_in.description is not None:
        task.description = task_in.description
    if task_in.status is not None:
        if task_in.status not in ("created", "in_progress", "completed"):
            raise ValueError(f"Invalid status: {task_in.status}")
        task.status = task_in.status

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: str) -> bool:
    task = get_task(db, task_id)
    if not task:
        return False
    db.delete(task)
    db.commit()
    return True
