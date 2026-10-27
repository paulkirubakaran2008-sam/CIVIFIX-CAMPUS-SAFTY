from datetime import UTC, datetime, timedelta
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from .campuses import campus_name
from .config import get_settings
from .schemas import UserPublic

password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer()

# Prototype accounts are explicit demo data across two campuses, so campus
# isolation can be demonstrated end to end. Production should replace this
# with persisted, hashed-password accounts (pwdlib is already wired up for
# that migration; see hash_password/verify_password below).
DEMO_USERS = [
    {"id": "user-student-001", "name": "Aarav Sharma", "email": "student@civicfix.edu", "password": "Student@123", "role": "student", "campus_id": "main-campus"},
    {"id": "user-admin-001", "name": "Campus Operations", "email": "admin@civicfix.edu", "password": "Admin@123", "role": "admin", "campus_id": "main-campus"},
    {"id": "user-student-002", "name": "Priya Menon", "email": "student.north@civicfix.edu", "password": "Student@123", "role": "student", "campus_id": "north-campus"},
    {"id": "user-admin-002", "name": "North Gate Operations", "email": "admin.north@civicfix.edu", "password": "Admin@123", "role": "admin", "campus_id": "north-campus"},
]


def hash_password(plain: str) -> str:
    return password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)


def make_token(user: dict) -> str:
    settings = get_settings()
    payload = {"sub": user["id"], "role": user["role"], "campus_id": user["campus_id"], "exp": datetime.now(UTC) + timedelta(hours=8)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def authenticate(email: str, password: str) -> dict | None:
    # Prototype accounts are explicit demo data; production should persist hashed passwords.
    return next((u for u in DEMO_USERS if u["email"] == email.lower() and u["password"] == password), None)


def public_user(user: dict) -> UserPublic:
    return UserPublic(id=user["id"], name=user["name"], email=user["email"], role=user["role"], campus_id=user["campus_id"], campus_name=campus_name(user["campus_id"]))


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> UserPublic:
    try:
        payload = jwt.decode(credentials.credentials, get_settings().jwt_secret, algorithms=["HS256"])
        user = next(u for u in DEMO_USERS if u["id"] == payload["sub"])
        return public_user(user)
    except (jwt.PyJWTError, StopIteration, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")


def require_admin(user: UserPublic = Depends(get_current_user)) -> UserPublic:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")
    return user
