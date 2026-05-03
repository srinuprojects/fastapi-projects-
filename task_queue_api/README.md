# Task Queue API — FastAPI + Celery + Redis

A production-style async job processing system. Submit long-running jobs (email, image processing, reports) via REST API and poll their status — without blocking the HTTP request.

## Architecture

```
Client
  │
  ▼
FastAPI (port 8000)          ← submit jobs, poll status
  │
  ├─► Redis (broker)         ← job queue
  │
  ├─► Celery Workers         ← consume & execute jobs
  │     ├── send_email
  │     ├── process_image
  │     └── generate_report
  │
  ├─► Celery Beat            ← scheduled jobs (cron)
  │
  └─► Flower (port 5555)     ← real-time monitoring UI
```

## Features

- **Async job submission** — POST a job, get a `task_id` back immediately
- **Status polling** — GET `/jobs/{task_id}` to check PENDING → STARTED → SUCCESS/FAILURE
- **Automatic retries** — exponential backoff on transient failures (3 retries)
- **Scheduled tasks** — Celery Beat runs daily report at 8 AM UTC
- **Job cancellation** — DELETE `/jobs/{task_id}` to revoke a queued job
- **Monitoring** — Flower dashboard shows worker health, task history, queue depth
- **Soft time limits** — tasks are killed cleanly if they run too long

## Quick Start

### With Docker (recommended)

```bash
docker-compose up --build
```

Services:
| Service | URL |
|---------|-----|
| FastAPI docs | http://localhost:8000/docs |
| Flower dashboard | http://localhost:5555 |
| Redis | localhost:6379 |

### Without Docker

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Redis
redis-server

# 3. Start the API
uvicorn app.main:app --reload

# 4. Start a Celery worker
celery -A app.core.celery_app.celery_app worker --loglevel=info

# 5. Start Celery Beat (scheduler)
celery -A app.core.celery_app.celery_app beat --loglevel=info

# 6. Start Flower (optional monitoring)
celery -A app.core.celery_app.celery_app flower
```

## API Usage

### Submit an email job
```bash
curl -X POST http://localhost:8000/jobs/email \
  -H "Content-Type: application/json" \
  -d '{"to": "user@example.com", "subject": "Hello", "body": "World"}'

# Response
{"task_id": "abc-123", "status": "PENDING", "message": "Email job queued for user@example.com"}
```

### Poll job status
```bash
curl http://localhost:8000/jobs/abc-123

# While running
{"task_id": "abc-123", "status": "STARTED", "result": null}

# On success
{"task_id": "abc-123", "status": "SUCCESS", "result": {"status": "sent", "message_id": "msg-abc123"}}
```

### Submit an image processing job
```bash
curl -X POST http://localhost:8000/jobs/image \
  -H "Content-Type: application/json" \
  -d '{"filename": "photo.jpg", "operations": ["resize", "compress"]}'
```

### Submit a report job
```bash
curl -X POST http://localhost:8000/jobs/report \
  -H "Content-Type: application/json" \
  -d '{"type": "daily_summary"}'
```

### Cancel a job
```bash
curl -X DELETE http://localhost:8000/jobs/abc-123
```

### Worker stats
```bash
curl http://localhost:8000/workers/stats
```

## Project Structure

```
task_queue_api/
├── app/
│   ├── core/
│   │   ├── config.py        # Settings (pydantic-settings)
│   │   └── celery_app.py    # Celery config + Beat schedule
│   ├── workers/
│   │   └── tasks.py         # send_email, process_image, generate_report
│   ├── schemas.py           # Pydantic request/response models
│   └── main.py              # FastAPI app + all endpoints
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Key Concepts Demonstrated

| Concept | Where |
|---------|-------|
| Async task queue | `celery_app.py` + `tasks.py` |
| Retry with backoff | `max_retries`, `countdown` in each task |
| Scheduled jobs | `beat_schedule` in `celery_app.py` |
| Result backend | Redis db/1 stores task results |
| Task routing | Each task type goes to a named queue |
| Soft time limits | `soft_time_limit` + `SoftTimeLimitExceeded` |
| Monitoring | Flower at :5555 |
