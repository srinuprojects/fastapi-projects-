from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from email_utils import send_verification_email, send_welcome_email
from config import settings
import uuid

app = FastAPI(title="Email Verification — Production Style")

pwd_context = CryptContext(schemes=["bcrypt"])

# ─────────────────────────────────────────
# In-memory database (replace with PostgreSQL in production)
#
# fake_db structure:
# {
#   "srinu@gmail.com": {
#       "username":    "srinu",
#       "email":       "srinu@gmail.com",
#       "password":    "$2b$...",
#       "is_verified": False,
#       "token":       "abc-123-xyz"
#   }
# }
# ─────────────────────────────────────────
fake_db: dict = {}


# ─────────────────────────────────────────
# Token helpers
# ─────────────────────────────────────────
def generate_verification_token(email: str) -> str:
    # Token contains email + expiry (24 hours)
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]   # returns email
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

def create_login_token(email: str) -> str:
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


# ─────────────────────────────────────────
# Request models
# ─────────────────────────────────────────
class RegisterRequest(BaseModel):
    username:  str
    email:     EmailStr    # pydantic validates email format automatically
    password:  str

class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


# ─────────────────────────────────────────
# Routes
# ─────────────────────────────────────────
@app.get("/")
def home():
    return {
        "message": "Email Verification App",
        "flow": [
            "1. POST /register    → creates account, sends verification email",
            "2. Check your email  → click the verification link",
            "3. GET /verify-email → account is verified",
            "4. POST /login       → login (only works after verification)",
            "5. GET /profile      → access protected route"
        ]
    }


@app.post("/register")
def register(data: RegisterRequest, background_tasks: BackgroundTasks):
    # Check if email already registered
    if data.email in fake_db:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed_password = pwd_context.hash(data.password)

    # Generate verification token
    token = generate_verification_token(data.email)

    # Save user — is_verified is False until they click the link
    fake_db[data.email] = {
        "username":    data.username,
        "email":       data.email,
        "password":    hashed_password,
        "is_verified": False,          # ← not verified yet
        "token":       token
    }

    # Send verification email in background (non-blocking)
    # User gets instant response, email sends in background
    background_tasks.add_task(
        send_verification_email,
        data.email,
        data.username,
        token
    )

    return {
        "message": f"Registration successful! Check {data.email} for verification link.",
        "note":    "You must verify your email before logging in."
    }


@app.get("/verify-email")
def verify_email(token: str, background_tasks: BackgroundTasks):
    # Decode token → get email
    email = verify_token(token)

    # Check user exists
    user = fake_db.get(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check already verified
    if user["is_verified"]:
        return {"message": "Email already verified. Please login."}

    # Mark as verified
    fake_db[email]["is_verified"] = True
    fake_db[email]["token"]       = None   # token is used, clear it

    # Send welcome email in background
    background_tasks.add_task(
        send_welcome_email,
        email,
        user["username"]
    )

    return {
        "message": f"Email verified successfully! Welcome {user['username']}!",
        "next":    "You can now login at POST /login"
    }


@app.post("/login")
def login(data: LoginRequest):
    # Check user exists
    user = fake_db.get(data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check password
    if not pwd_context.verify(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Block login if email not verified
    if not user["is_verified"]:
        raise HTTPException(
            status_code=403,
            detail="Email not verified. Please check your inbox and verify first."
        )

    # Create JWT token
    token = create_login_token(data.email)
    return {
        "access_token": token,
        "token_type":   "bearer",
        "message":      f"Welcome back {user['username']}!"
    }


@app.post("/resend-verification")
def resend_verification(email: EmailStr, background_tasks: BackgroundTasks):
    # Allow user to request a new verification email
    user = fake_db.get(email)
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")

    if user["is_verified"]:
        return {"message": "Email is already verified. Please login."}

    # Generate fresh token
    new_token = generate_verification_token(email)
    fake_db[email]["token"] = new_token

    background_tasks.add_task(
        send_verification_email,
        email,
        user["username"],
        new_token
    )

    return {"message": f"Verification email resent to {email}"}


@app.get("/profile")
def profile(email: str):
    user = fake_db.get(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user["is_verified"]:
        raise HTTPException(status_code=403, detail="Email not verified")

    return {
        "username":    user["username"],
        "email":       user["email"],
        "is_verified": user["is_verified"]
    }
