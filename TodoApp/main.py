import requests
from fastapi import FastAPI, HTTPException, Depends, Path, status
from pydantic import BaseModel, Field
import models
from database import SessionLocal, engine
from typing import Annotated, TypeAlias
from sqlalchemy.orm import Session
from routers import auth
from routers.auth import get_current_user

app = FastAPI()
app.include_router(auth.router)


# In WSL2, Windows host IP is the default gateway (not the nameserver)
def _get_ollama_host() -> str:
    try:
        import subprocess
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True, text=True
        )
        # Output: "default via 172.x.x.x dev eth0 ..."
        return result.stdout.split()[2]
    except Exception:
        pass
    return "localhost"

OLLAMA_URL = f"http://{_get_ollama_host()}:11434/api/generate"

models.Base.metadata.create_all(bind=engine)

# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency: TypeAlias = Annotated[Session, Depends(get_db)]
user_dependency: TypeAlias = Annotated[dict, Depends(get_current_user)]

# Request Model
class TodoCreate(BaseModel):
    title: str = Field(min_length=10)
    description: str = Field(min_length=20)
    completed: bool = False


@app.get("/")
def home():
    return {"message": "AI Chat API is running"}


@app.get("/chat")
def chat(prompt: str):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()


# Get all todos for the authenticated user
@app.get("/todos")
async def read_all_todos(db: db_dependency, user: user_dependency):
    return db.query(models.Todos).filter(models.Todos.owner_id == user["id"]).all()


# Get one todo (must belong to the authenticated user)
@app.get("/todo/{todo_id}")
async def read_todo(db: db_dependency, user: user_dependency, todo_id: int = Path(gt=0)):
    todo = db.query(models.Todos).filter(
        models.Todos.id == todo_id,
        models.Todos.owner_id == user["id"]
    ).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


# Create a todo and associate it with the authenticated user
@app.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(db: db_dependency, user: user_dependency, todo: TodoCreate):
    todo_model = models.Todos(**todo.model_dump(), owner_id=user["id"])
    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)
    return todo_model


# Update a todo (only the owner can update)
@app.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(db: db_dependency, user: user_dependency, todo: TodoCreate, todo_id: int = Path(gt=0)):
    todo_model = db.query(models.Todos).filter(
        models.Todos.id == todo_id,
        models.Todos.owner_id == user["id"]
    ).first()
    if not todo_model:
        raise HTTPException(status_code=404, detail="Todo not found")

    for key, value in todo.model_dump().items():
        setattr(todo_model, key, value)
    db.commit()


# Delete a todo (only the owner can delete)
@app.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, user: user_dependency, todo_id: int = Path(gt=0)):
    todo_model = db.query(models.Todos).filter(
        models.Todos.id == todo_id,
        models.Todos.owner_id == user["id"]
    ).first()
    if not todo_model:
        raise HTTPException(status_code=404, detail="Todo not found")

    db.delete(todo_model)
    db.commit()
