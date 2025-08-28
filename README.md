# Менеджер задач c с тестами
- запуск максимально прост:
    1. клонировать репозиторий `git clone https://github.com/BOPOH1243/ttFastapiTasksManager.git`
    2. запустить через docker-compose `sudo docker-compose up -d`
    3. в докере проброшен nginx на 80 порт, так что всё доступно по адресу `https://localhost/docs`
- проект сделан по одному моему древнему шаблону, так что в нем есть некоторые избыточности и откровенно лишние вещи

## Подробности и детали решения:
1. Использован менеджер миграций alembic
2. Для тестов используется in memory бд sqlite, однако сам проект сделан с применением postgresql.
    - из-за этого uuid генерится немного нетипично - строкой, ибо sqlite не имеет uuid, а postgresql не развернуть отдельно для тестов в памяти ~но в целом всё правильно~
3. приложение сделано на fastapi, а тесты на pytest (pytest-cov), ибо мой шаблон под pytest заточен

# вот примерная структура проекта:
~да, туда попал venv и alembic, чего еще можно ожидать от `tree -L 2 > README.md`~
```
.
├── alembic
│   ├── env.py
│   ├── __pycache__
│   ├── README
│   ├── script.py.mako
│   └── versions
├── alembic.ini
├── app
│   ├── db.py
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── __pycache__
│   ├── routes
│   ├── schemas.py
│   ├── services.py
│   └── settings.py
├── docker-compose copy.ym
├── docker-compose.yml
├── dockerfile
├── nginx.conf
├── README.md
├── requirements.txt
├── tests
│   ├── conftest.py
│   ├── __init__.py
│   ├── __pycache__
│   ├── test_services.py
│   └── test_tasks.py
├── venv
│   ├── bin
│   ├── include
│   ├── lib
│   ├── lib64 -> lib
│   └── pyvenv.cfg
└── wait-for-it.sh

14 directories, 23 files
```