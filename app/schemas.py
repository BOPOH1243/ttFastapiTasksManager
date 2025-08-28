from typing import Optional
from pydantic import BaseModel, Field, constr


ALLOWED_STATUSES = ("created", "in_progress", "completed")


class TaskBase(BaseModel):
    title: constr(min_length=1) = Field(..., example="Buy milk")
    description: Optional[str] = Field("", example="2 liters, whole milk")


class TaskCreate(TaskBase):
    status: Optional[str] = Field("created", description=f"One of {ALLOWED_STATUSES}")

    class Config:
        schema_extra = {
            "example": {
                "title": "Write tests",
                "description": "Write unit tests for tasks",
                "status": "created",
            }
        }


class TaskUpdate(BaseModel):
    title: Optional[constr(min_length=1)]
    description: Optional[str]
    status: Optional[str]

    class Config:
        schema_extra = {
            "example": {"description": "updated description", "status": "in_progress"}
        }


class TaskOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: str

    class Config:
        orm_mode = True
