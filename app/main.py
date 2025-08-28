from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import tasks

app = FastAPI(title="Task Manager", version="0.1.0", docs_url="/docs", openapi_url="/openapi.json")

# CORS - полностью отключен для тестирования, не рекомендуется для прода
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
