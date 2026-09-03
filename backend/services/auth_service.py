from sqlalchemy import select
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password, verify_password
from models.user import User
from schemas.auth import LoginRequest, RegisterRequest


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


def register_user(db: Session, request: RegisterRequest) -> User:
    existing = db.scalar(select(User).where(User.email == request.email))
    if existing is not None:
        raise EmailAlreadyRegisteredError(request.email)

    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        name=request.name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, request: LoginRequest) -> User:
    user = db.scalar(select(User).where(User.email == request.email))
    if user is None or not verify_password(request.password, user.password_hash):
        raise InvalidCredentialsError()
    return user


def issue_token_for(user: User) -> str:
    return create_access_token(subject=str(user.id))
