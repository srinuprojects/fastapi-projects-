from pydantic import BaseModel, EmailStr, Field
from typing import Any, Optional
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class EmailJobRequest(BaseModel):
    to: EmailStr
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)


class ImageJobRequest(BaseModel):
    filename: str = Field(..., description="Name of the uploaded image file")
    operations: list[str] = Field(
        default=["resize", "compress"],
        description="List of operations to apply",
    )


class ReportJobRequest(BaseModel):
    type: str = Field(default="custom", description="Report type: daily_summary, custom")
    filters: Optional[dict[str, Any]] = None


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
