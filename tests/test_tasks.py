import uuid as _uuid
from typing import Any, Dict, List, Optional

import pytest


def _extract_uuid_from_obj(obj: Dict[str, Any]) -> Optional[str]:
    """
    Попробовать найти поле, содержащее UUID в ответе.
    Поддерживаем варианты названий полей: "id", "uuid", "task_id".
    """
    for key in ("id", "uuid", "task_id"):
        v = obj.get(key)
        if isinstance(v, str):
            try:
                _uuid.UUID(v)
                return v
            except Exception:
                pass
    # Попробуем все строковые поля
    for k, v in obj.items():
        if isinstance(v, str):
            try:
                _uuid.UUID(v)
                return v
            except Exception:
                continue
    return None


def _get_task_url(base: str = "/tasks", task_id: Optional[str] = None) -> str:
    return f"{base}/{task_id}" if task_id else base


def test_openapi_and_docs_available(client):
    """/openapi.json и /docs должны быть доступны (swagger)."""
    r = client.get("/openapi.json")
    assert r.status_code == 200, "openapi.json не доступен"
    data = r.json()
    assert "paths" in data and isinstance(data["paths"], dict)

    # краткая проверка на наличие пути /tasks в openapi (если есть)
    # не делаем жёсткого требования, просто информативно — если endpoint есть, он попадёт в spec
    # также проверим /docs (UI)
    r_docs = client.get("/docs")
    assert r_docs.status_code in (200, 307, 308, 401), "Swagger UI (/docs) недоступен (ожидали 200/307/308/401)"


def test_create_task_minimal_and_response_shape(client):
    """Создание задачи — возвращается uuid/id, title, description, status."""
    payload = {"title": "Test task", "description": "описание задачи"}
    r = client.post("/tasks", json=payload)
    assert r.status_code in (200, 201), f"POST /tasks вернул {r.status_code}, ожидали 200/201"
    data = r.json()
    # Проверяем поля title/description
    assert data.get("title") == payload["title"]
    assert data.get("description") == payload["description"]
    # UUID присутствует в каком-то поле
    uid = _extract_uuid_from_obj(data)
    assert uid is not None, f"В ответе нет uuid/id: {data}"
    # Статус присутствует и это строка
    assert "status" in data and isinstance(data["status"], str)


def test_create_task_requires_title(client):
    """Валидация: если нет title — возвращается 422 (или 400)"""
    payload = {"description": "нет названия"}
    r = client.post("/tasks", json=payload)
    # FastAPI обычно возвращает 422 за body validation
    assert r.status_code in (400, 422), f"Ожидали 400/422 при отсутствии title, получили {r.status_code}"


def test_get_single_task_by_id(client):
    """Создать задачу, получить её по UUID."""
    payload = {"title": "Get me", "description": "single get"}
    r = client.post("/tasks", json=payload)
    assert r.status_code in (200, 201)
    created = r.json()
    task_id = _extract_uuid_from_obj(created)
    assert task_id is not None

    r2 = client.get(f"/tasks/{task_id}")
    assert r2.status_code == 200
    got = r2.json()
    # Совпадают title/description и id
    assert got.get("title") == payload["title"]
    assert got.get("description") == payload["description"]
    # id совпадает
    got_id = _extract_uuid_from_obj(got)
    assert got_id == task_id


def test_get_list_returns_created_tasks(client):
    """GET /tasks возвращает список, содержащий ранее созданные задачи."""
    # создаём две задачи
    tasks_payloads = [
        {"title": "List task 1", "description": "d1"},
        {"title": "List task 2", "description": "d2"},
    ]
    created_ids = []
    for p in tasks_payloads:
        r = client.post("/tasks", json=p)
        assert r.status_code in (200, 201)
        created_ids.append(_extract_uuid_from_obj(r.json()))

    r_list = client.get("/tasks")
    assert r_list.status_code == 200
    body = r_list.json()
    assert isinstance(body, list), "Ожидали список задач от GET /tasks"
    # Проверим, что все наши id есть в возвращаемом списке
    returned_ids = { _extract_uuid_from_obj(item) for item in body if isinstance(item, dict) }
    for cid in created_ids:
        assert cid in returned_ids, f"Созданная задача {cid} не найдена в GET /tasks"


def test_update_task_partial_and_full(client):
    """Обновление задачи: пробуем PATCH, если нет — PUT. Проверяем, что данные изменяются."""
    payload = {"title": "To update", "description": "orig"}
    r = client.post("/tasks", json=payload)
    assert r.status_code in (200, 201)
    created = r.json()
    task_id = _extract_uuid_from_obj(created)
    assert task_id

    # Попробуем PATCH (частичное обновление)
    patch_payload = {"description": "updated"}
    r_patch = client.patch(f"/tasks/{task_id}", json=patch_payload)
    if r_patch.status_code in (200, 204):
        # если 204 — получить обновлённый ресурс
        if r_patch.status_code == 204:
            r_get = client.get(f"/tasks/{task_id}")
            assert r_get.status_code == 200
            data = r_get.json()
        else:
            data = r_patch.json()
        assert data.get("description") == "updated"
    else:
        # Попробуем PUT (полное обновление)
        put_payload = {"title": "To update", "description": "updated", "status": created.get("status")}
        r_put = client.put(f"/tasks/{task_id}", json=put_payload)
        assert r_put.status_code in (200, 204)
        if r_put.status_code == 200:
            data = r_put.json()
            assert data.get("description") == "updated"
        else:
            # 204 -> заберём ресурс
            r_get = client.get(f"/tasks/{task_id}")
            assert r_get.status_code == 200
            assert r_get.json().get("description") == "updated"


def test_delete_task_and_idempotency(client):
    """Удаление задачи: удаляем — затем проверяем 404 при повторном запросе."""
    payload = {"title": "To delete", "description": "will be deleted"}
    r = client.post("/tasks", json=payload)
    assert r.status_code in (200, 201)
    task_id = _extract_uuid_from_obj(r.json())
    assert task_id

    r_del = client.delete(f"/tasks/{task_id}")
    assert r_del.status_code in (200, 204)

    # При последующем GET ожидаем 404
    r_get = client.get(f"/tasks/{task_id}")
    assert r_get.status_code in (404, 422), "После удаления ожидали 404/422 при GET"

    # Повторное удаление может вернуть 404 или 204 — принимаем оба варианта
    r_del2 = client.delete(f"/tasks/{task_id}")
    assert r_del2.status_code in (404, 204, 200)


def test_get_with_invalid_uuid_returns_4xx(client):
    """GET /tasks/{id} с невалидным UUID — ожидаем ошибку 4xx."""
    r = client.get("/tasks/not-a-uuid")
    assert r.status_code in (400, 404, 422)


@pytest.mark.parametrize("status_value", ["created", "in_progress", "completed"])
def test_create_with_allowed_statuses(client, status_value):
    """
    Если API поддерживает передачу статуса при создании — должно работать для допустимых значений.
    (Этот тест служит для спецификации возможного поведения; возможно, ваш API
    игнорирует поле status при create — тогда этот тест можно откорректировать.)
    """
    payload = {"title": f"Status {status_value}", "description": "s", "status": status_value}
    r = client.post("/tasks", json=payload)
    assert r.status_code in (200, 201)
    data = r.json()
    # Если API вернул поле status, оно должно равняться переданному
    if "status" in data:
        assert data["status"] == status_value
