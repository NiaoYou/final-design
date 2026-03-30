from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.task import Task


def create_task(
    db: Session,
    *,
    task_name: str,
    status: str,
    file_path: str,
    result_path: str,
) -> Task:
    task = Task(
        task_name=task_name,
        status=status,
        file_path=file_path,
        result_path=result_path,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task_status(db: Session, task_id: int, *, status: str, error_message: str | None = None) -> Task:
    task = get_task(db, task_id)
    task.status = status
    if error_message is not None:
        task.error_message = error_message
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise ValueError(f"Task 不存在: {task_id}")
    return task


def list_tasks(db: Session, *, skip: int = 0, limit: int = 50) -> list[Task]:
    return db.query(Task).order_by(Task.id.desc()).offset(skip).limit(limit).all()

