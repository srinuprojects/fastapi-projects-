from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

app = FastAPI(title="Level 3 - Role Based Access Control (RBAC)")

# ─────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────
SECRET_KEY     = "mysecretkey123"
ALGORITHM      = "HS256"
EXPIRY_MINUTES = 30

pwd_context   = CryptContext(schemes=["bcrypt"])
bearer_scheme = HTTPBearer()

fake_db: dict = {}


# ─────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_jwt_token(username: str, role: str) -> str:
    payload = {
        "sub":  username,
        "role": role,      # ← role is now stored INSIDE the token
        "exp":  datetime.utcnow() + timedelta(minutes=EXPIRY_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload   # returns {"sub": "srinu", "role": "admin", "exp": ...}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ─────────────────────────────────────────
# Base dependency — any logged in user
# ─────────────────────────────────────────
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token   = credentials.credentials
    payload = verify_jwt_token(token)
    username = payload["sub"]

    user = fake_db.get(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ─────────────────────────────────────────
# Role checker — factory function
# Returns a dependency that checks for a specific role
#
# Usage:
#   Depends(require_role("admin"))  → only admin can enter
#   Depends(require_role("user"))   → only user can enter
# ─────────────────────────────────────────
def require_role(*allowed_roles: str):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,   # 403 = Forbidden (logged in but not allowed)
                detail=f"Access denied. Required role: {allowed_roles}, your role: {current_user['role']}"
            )
        return current_user
    return role_checker


# ─────────────────────────────────────────
# Request models
# ─────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "user"   # default role is "user", can pass "admin" or "guest"

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

    # Validate role
    if data.role not in ["admin", "user", "guest"]:
        raise HTTPException(status_code=400, detail="Role must be: admin, user, or guest")

    fake_db[data.username] = {
        "username": data.username,
        "password": hash_password(data.password),
        "role":     data.role
    }
    return {"message": f"User '{data.username}' registered with role '{data.role}'"}


@app.post("/login")
def login(data: LoginRequest):
    user = fake_db.get(data.username)
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Role is included in the token
    token = create_jwt_token(data.username, user["role"])
    return {
        "access_token": token,
        "token_type":   "bearer",
        "role":         user["role"]
    }


# ─────────────────────────────────────────
# Public route — anyone can access (no token needed)
# ─────────────────────────────────────────
@app.get("/public")
def public():
    return {"message": "This is public. Anyone can see this."}


# ─────────────────────────────────────────
# User route — any logged in user (admin, user, guest)
# ─────────────────────────────────────────
@app.get("/dashboard")
def dashboard(current_user: dict = Depends(require_role("admin", "user", "guest"))):
    return {"message": f"Welcome to dashboard, {current_user['username']}! Your role: {current_user['role']}"}


# ─────────────────────────────────────────
# User + Admin route — only admin and user (not guest)
# ─────────────────────────────────────────
@app.get("/profile")
def profile(current_user: dict = Depends(require_role("admin", "user"))):
    return {"message": f"Your profile, {current_user['username']}. Role: {current_user['role']}"}


# ─────────────────────────────────────────
# Admin only route — strictly admin
# ─────────────────────────────────────────
@app.get("/admin/users")
def admin_get_users(current_user: dict = Depends(require_role("admin"))):
    # Return all users (without passwords)
    users = [{"username": u["username"], "role": u["role"]} for u in fake_db.values()]
    return {"total_users": len(users), "users": users}


@app.delete("/admin/delete/{username}")
def admin_delete_user(username: str, current_user: dict = Depends(require_role("admin"))):
    if username not in fake_db:
        raise HTTPException(status_code=404, detail="User not found")
    del fake_db[username]
    return {"message": f"User '{username}' deleted by admin '{current_user['username']}'"}


@app.get("/")
def home():
    return {
        "message": "Level 3 - RBAC",
        "roles": ["admin", "user", "guest"],
        "routes": {
            "GET  /public":              "everyone (no token)",
            "GET  /dashboard":           "admin + user + guest",
            "GET  /profile":             "admin + user only",
            "GET  /admin/users":         "admin only",
            "DELETE /admin/delete/{id}": "admin only"
        }
    }
