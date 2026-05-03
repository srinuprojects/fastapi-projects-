from fastapi import FastAPI, HTTPException
from celery.result import AsyncResult

from app.core.config import settings
from app.core.celery_app import celery_app
from app.schemas import (
    EmailJobRequest, ImageJobRequest, ReportJobRequest,
    TaskResponse, TaskStatusResponse, TaskStatus,
)
from app.workers.tasks import send_email, process_image, generate_report

app = FastAPI(
    title=settings.APP_NAME,
    description="Async job queue API using FastAPI + Celery + Redis",
    version="1.0.0",
)


# ── Health ──────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health_check():
    try:
        celery_app.control.ping(timeout=1)
        worker_status = "online"
    except Exception:
        worker_status = "offline"
    return {"api": "ok", "workers": worker_status}


# ── Jobs ────────────────────────────────────────────────────────────────────

@app.post("/jobs/email", response_model=TaskResponse, tags=["Jobs"])
def submit_email_job(request: EmailJobRequest):
    """Submit an async email sending job."""
    task = send_email.delay(request.model_dump())
    return TaskResponse(
        task_id=task.id,
        status=TaskStatus.PENDING,
        message=f"Email job queued for {request.to}",
    )


@app.post("/jobs/image", response_model=TaskResponse, tags=["Jobs"])
def submit_image_job(request: ImageJobRequest):
    """Submit an async image processing job."""
    task = process_image.delay(request.model_dump())
    return TaskResponse(
        task_id=task.id,
        status=TaskStatus.PENDING,
        message=f"Image processing job queued for {request.filename}",
    )


@app.post("/jobs/report", response_model=TaskResponse, tags=["Jobs"])
def submit_report_job(request: ReportJobRequest):
    """Submit an async report generation job."""
    task = generate_report.delay(request.model_dump())
    return TaskResponse(
        task_id=task.id,
        status=TaskStatus.PENDING,
        message=f"Report generation job queued (type={request.type})",
    )


# ── Status & Control ────────────────────────────────────────────────────────

@app.get("/jobs/{task_id}", response_model=TaskStatusResponse, tags=["Jobs"])
def get_job_status(task_id: str):
    """Poll the status and result of any submitted job."""
    result = AsyncResult(task_id, app=celery_app)

    if result.state == "FAILURE":
        return TaskStatusResponse(
            task_id=task_id,
            status=TaskStatus.FAILURE,
            error=str(result.info),
        )

    return TaskStatusResponse(
        task_id=task_id,
        status=TaskStatus(result.state),
        result=result.result if result.ready() else None,
    )


@app.delete("/jobs/{task_id}", tags=["Jobs"])
def revoke_job(task_id: str, terminate: bool = False):
    """Cancel a pending or running job."""
    celery_app.control.revoke(task_id, terminate=terminate)
    return {"task_id": task_id, "status": "revoked"}


@app.get("/workers/stats", tags=["Workers"])
def worker_stats():
    """Get active worker info and queue lengths."""
    inspector = celery_app.control.inspect(timeout=2)
    return {
        "active_tasks": inspector.active() or {},
        "registered_tasks": inspector.registered() or {},
        "stats": inspector.stats() or {},
    }
