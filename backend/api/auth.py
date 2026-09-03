from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from core.rate_limit import rate_limit
from models.user import User
from schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from schemas.user import UserRead
from services.audit_service import record_event
from services.auth_service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    authenticate_user,
    issue_token_for,
    register_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Auth endpoints are the most common brute-force / enumeration target, so
# they get a tighter budget than the rest of the API.
register_rate_limit = rate_limit("auth-register", max_requests=5, window_seconds=60)
login_rate_limit = rate_limit("auth-login", max_requests=10, window_seconds=60)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(register_rate_limit)],
)
def register(request: RegisterRequest, req: Request, db: Session = Depends(get_db)) -> TokenResponse:
    client_ip = req.client.host if req.client else None
    try:
        user = register_user(db, request)
    except EmailAlreadyRegisteredError as exc:
        record_event(db, "register_failed_duplicate_email", ip_address=client_ip)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        ) from exc

    record_event(db, "register_success", user_id=user.id, ip_address=client_ip)
    token = issue_token_for(user)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(login_rate_limit)])
def login(request: LoginRequest, req: Request, db: Session = Depends(get_db)) -> TokenResponse:
    client_ip = req.client.host if req.client else None
    try:
        user = authenticate_user(db, request)
    except InvalidCredentialsError as exc:
        record_event(db, "login_failed", detail=request.email, ip_address=client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        ) from exc

    record_event(db, "login_success", user_id=user.id, ip_address=client_ip)
    token = issue_token_for(user)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
