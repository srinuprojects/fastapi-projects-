from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext

app = FastAPI(title="Level 1 - Basic Login")

# ─────────────────────────────────────────
# Password hashing setup
# bcrypt is the algorithm — industry standard for hashing passwords
# ─────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"])

def hash_password(plain_password: str) -> str:
    # Converts "mypassword" → "$2b$12$Kx8...abc" (irreversible)
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Checks if plain password matches the stored hash
    return pwd_context.verify(plain_password, hashed_password)


# ─────────────────────────────────────────
# Fake in-memory database (like a dictionary)
# In real projects this would be PostgreSQL/MySQL
# ─────────────────────────────────────────
fake_db: dict = {}
# Example after register:
# fake_db = {
#   "srinu": {"username": "srinu", "password": "$2b$12$Kx8...abc"}
# }


# ─────────────────────────────────────────
# Request models
# ─────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str


# ─────────────────────────────────────────
# Routes
# ─────────────────────────────────────────

@app.post("/register")
def register(data: RegisterRequest):
    # Check if username already exists
    if data.username in fake_db:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash the password before saving — NEVER save plain text
    hashed = hash_password(data.password)

    # Save user to fake database
    fake_db[data.username] = {
        "username": data.username,
        "password": hashed        # storing hashed, not plain
    }

    return {"message": f"User '{data.username}' registered successfully"}


@app.post("/login")
def login(data: LoginRequest):
    # Step 1: Check if user exists
    user = fake_db.get(data.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Step 2: Verify password against stored hash
    if not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Step 3: Login success
    return {"message": f"Welcome {data.username}! Login successful."}


@app.get("/profile/{username}")
def profile(username: str):
    # Check if user exists
    user = fake_db.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Never return the password — even hashed
    return {"username": user["username"], "message": "This is your profile"}


@app.get("/")
def home():
    return {
        "message": "Level 1 - Basic Login",
        "endpoints": {
            "POST /register": "Create a new account",
            "POST /login":    "Login with username & password",
            "GET  /profile/{username}": "View profile"
        }
    }
