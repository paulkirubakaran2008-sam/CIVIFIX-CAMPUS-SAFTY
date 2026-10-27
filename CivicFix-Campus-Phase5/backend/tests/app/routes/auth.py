from fastapi import APIRouter, HTTPException, status
from ..auth import authenticate, make_token, public_user
from ..schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    user = authenticate(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return TokenResponse(access_token=make_token(user), user=public_user(user))
