import uuid
from sqlalchemy import Column, String, Text
from app.db import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True, default="")
    status = Column(String(50), nullable=False, default="created") #"created", "in_progress", "completed"
