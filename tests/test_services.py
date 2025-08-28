# tests/test_services.py
import pytest
from sqlalchemy.orm import Session
from app import models, schemas, services
from pydantic import ValidationError

def test_create_task_valid_statuses(db_session: Session):
    """Создание задач с разными допустимыми статусами."""
    for status in ("created", "in_progress", "completed"):
        task_in = schemas.TaskCreate(title=f"Task {status}", description="desc", status=status)
        task = services.create_task(db_session, task_in)
        assert isinstance(task, models.Task)
        assert task.title == f"Task {status}"
        assert task.status == status
        # Проверим, что задача реально сохранилась в БД
        from_db = services.get_task(db_session, task.id)
        assert from_db is not None
        assert from_db.id == task.id


def test_create_task_invalid_status_raises(db_session: Session):
    """Недопустимый статус вызывает ValueError."""
    bad_task = schemas.TaskCreate(title="Bad", description="bad", status="wrong_status")
    with pytest.raises(ValueError) as e:
        services.create_task(db_session, bad_task)
    assert "Invalid status" in str(e.value)


def test_get_task_existing_and_non_existing(db_session: Session):
    """get_task возвращает задачу если она есть, и None если нет."""
    task_in = schemas.TaskCreate(title="Get me", description="desc")
    created = services.create_task(db_session, task_in)

    found = services.get_task(db_session, created.id)
    assert found is not None
    assert found.id == created.id

    not_found = services.get_task(db_session, "non-existent-id")
    assert not_found is None


def test_get_tasks_returns_all(db_session: Session):
    """get_tasks возвращает список задач, поддерживает skip/limit."""
    # создаём несколько задач
    for i in range(5):
        t = schemas.TaskCreate(title=f"Task {i}", description="x")
        services.create_task(db_session, t)

    all_tasks = services.get_tasks(db_session)
    assert isinstance(all_tasks, list)
    assert len(all_tasks) == 5

    limited = services.get_tasks(db_session, skip=0, limit=2)
    assert len(limited) == 2
    # проверим что это Task объекты
    assert all(isinstance(t, models.Task) for t in limited)


def test_update_task_success(db_session: Session):
    """Обновление существующей задачи меняет поля."""
    task_in = schemas.TaskCreate(title="Old title", description="old desc")
    created = services.create_task(db_session, task_in)

    update_data = schemas.TaskUpdate(title="New title", description="new desc", status="completed")
    updated = services.update_task(db_session, created.id, update_data)

    assert updated is not None
    assert updated.title == "New title"
    assert updated.description == "new desc"
    assert updated.status == "completed"

    # перепроверим в БД
    from_db = services.get_task(db_session, created.id)
    assert from_db.title == "New title"


def test_update_task_invalid_status_raises(db_session):
    task_in = schemas.TaskCreate(title="Title", description="desc")
    created = services.create_task(db_session, task_in)

    with pytest.raises(ValidationError):
        schemas.TaskUpdate(status="bad_status")


def test_delete_task_success_and_idempotent(db_session: Session):
    """Удаление задачи возвращает True, повторное удаление — False."""
    task_in = schemas.TaskCreate(title="To delete", description="desc")
    created = services.create_task(db_session, task_in)

    # первая попытка удалить
    result = services.delete_task(db_session, created.id)
    assert result is True

    # задача исчезла
    assert services.get_task(db_session, created.id) is None

    # повторное удаление
    result2 = services.delete_task(db_session, created.id)
    assert result2 is False
