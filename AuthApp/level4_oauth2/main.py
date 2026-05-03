from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timedelta
import httpx

app = FastAPI(title="Level 4 - OAuth2 Login with Google")

# ─────────────────────────────────────────
# Your app's JWT config (same as before)
# ─────────────────────────────────────────
SECRET_KEY     = "mysecretkey123"
ALGORITHM      = "HS256"
EXPIRY_MINUTES = 30

bearer_scheme = HTTPBearer()

# In-memory user store
fake_db: dict = {}


# ─────────────────────────────────────────
# Google OAuth2 credentials
# To get these:
#   1. Go to https://console.cloud.google.com
#   2. Create a project
#   3. Go to APIs & Services → Credentials
#   4. Create OAuth2 Client ID (Web application)
#   5. Add redirect URI: http://localhost:8000/auth/google/callback
#   6. Copy CLIENT_ID and CLIENT_SECRET here
# ─────────────────────────────────────────
GOOGLE_CLIENT_ID     = "your-google-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "your-google-client-secret"
GOOGLE_REDIRECT_URI  = "http://localhost:8000/auth/google/callback"

# Google's OAuth2 URLs (these never change)
GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL  = "https://www.googleapis.com/oauth2/v3/userinfo"


# ─────────────────────────────────────────
# JWT helpers (same as Level 2 & 3)
# ─────────────────────────────────────────
def create_jwt_token(username: str, email: str, role: str = "user") -> str:
    payload = {
        "sub":   username,
        "email": email,
        "role":  role,
        "exp":   datetime.utcnow() + timedelta(minutes=EXPIRY_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    payload = verify_jwt_token(credentials.credentials)
    return payload


# ─────────────────────────────────────────
# Routes
# ─────────────────────────────────────────
@app.get("/")
def home():
    return {
        "message": "Level 4 - OAuth2 Login with Google",
        "how_to_use": [
            "1. GET /auth/google          → redirects you to Google login page",
            "2. Google redirects back     → GET /auth/google/callback (automatic)",
            "3. You get a JWT token       → use it on /profile"
        ]
    }


@app.get("/auth/google")
def login_with_google():
    # Step 1: Build the Google login URL and redirect user to it
    # scope=openid email profile → we want user's identity, email, and name
    google_login_url = (
        f"{GOOGLE_AUTH_URL}"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid email profile"
    )
    # Redirect user's browser to Google
    return RedirectResponse(url=google_login_url)


@app.get("/auth/google/callback")
async def google_callback(code: str):
    # Step 2: Google redirects back here with a "code"
    # Exchange the code for an access token from Google

    async with httpx.AsyncClient() as client:

        # Exchange code → token
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code":          code,
                "client_id":     GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri":  GOOGLE_REDIRECT_URI,
                "grant_type":    "authorization_code"
            }
        )
        token_data = token_response.json()

        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data["error"])

        google_access_token = token_data["access_token"]

        # Step 3: Use Google's token to get user info
        user_response = await client.get(
            GOOGLE_USER_URL,
            headers={"Authorization": f"Bearer {google_access_token}"}
        )
        google_user = user_response.json()

    # google_user looks like:
    # {
    #   "sub":     "1234567890",         ← Google's unique user ID
    #   "email":   "srinu@gmail.com",
    #   "name":    "Srinu",
    #   "picture": "https://..."
    # }

    email    = google_user["email"]
    username = google_user["name"]

    # Step 4: Save user in our DB (first time login = auto register)
    if email not in fake_db:
        fake_db[email] = {
            "username": username,
            "email":    email,
            "role":     "user",
            "provider": "google"   # came from Google login
        }

    # Step 5: Create our own JWT token and return it
    token = create_jwt_token(username, email)
    return {
        "message":      f"Welcome {username}!",
        "access_token": token,
        "token_type":   "bearer",
        "user": {
            "username": username,
            "email":    email,
            "role":     fake_db[email]["role"]
        }
    }


@app.get("/profile")
def profile(current_user: dict = Depends(get_current_user)):
    return {
        "message":  f"Hello {current_user['sub']}!",
        "email":    current_user["email"],
        "role":     current_user["role"]
    }
