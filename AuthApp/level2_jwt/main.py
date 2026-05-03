from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

app = FastAPI(title="Level 2 - JWT Authentication")

# ─────────────────────────────────────────
# JWT Configuration
# SECRET_KEY: used to sign the token — keep this secret in real apps!
# ALGORITHM:  HS256 is standard
# EXPIRY:     token dies after 30 minutes
# ─────────────────────────────────────────
SECRET_KEY = "mysecretkey123"
ALGORITHM  = "HS256"
EXPIRY_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"])
bearer_scheme = HTTPBearer()   # Reads "Authorization: Bearer <token>" from header

fake_db: dict = {}


# ─────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_jwt_token(username: str) -> str:
    # Payload = data inside the token
    payload = {
        "sub": username,                                         # subject (who is this token for)
        "exp": datetime.utcnow() + timedelta(minutes=EXPIRY_MINUTES)  # expiry time
    }
    # Sign the token with SECRET_KEY → produces the final JWT string
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_jwt_token(token: str) -> str:
    try:
        # Decode and verify the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]   # return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ─────────────────────────────────────────
# Dependency — protect routes with this
# FastAPI calls this automatically before the route runs
# ─────────────────────────────────────────
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    # credentials.credentials = the token string from "Authorization: Bearer <token>"
    token = credentials.credentials
    username = verify_jwt_token(token)

    user = fake_db.get(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


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
    if data.username in fake_db:
        raise HTTPException(status_code=400, detail="Username already exists")

    fake_db[data.username] = {
        "username": data.username,
        "password": hash_password(data.password)
    }
    return {"message": f"User '{data.username}' registered successfully"}


@app.post("/login")
def login(data: LoginRequest):
    user = fake_db.get(data.username)
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Create JWT token and return it
    token = create_jwt_token(data.username)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": f"{EXPIRY_MINUTES} minutes"
    }


@app.get("/profile")
def profile(current_user: dict = Depends(get_current_user)):
    # Depends(get_current_user) → automatically verifies token before entering here
    return {
        "username": current_user["username"],
        "message": "Token is valid! This is your protected profile."
    }


@app.get("/")
def home():
    return {
        "message": "Level 2 - JWT Authentication",
        "how_to_use": [
            "1. POST /register → create account",
            "2. POST /login → get JWT token",
            "3. GET /profile → send token in header: Authorization: Bearer <token>"
        ]
    }
