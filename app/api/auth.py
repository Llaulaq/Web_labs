from fastapi import APIRouter
from pydantic import BaseModel

from app.deps import AuthSvc, CurrentUser, Svc
from app.schemas import User, UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=User, status_code=201)
def register(service: Svc, payload: UserCreate):
    # Регистрация = создание пользователя; пароль хешируется в сервисе
    return service.create(payload)


@router.post("/login", response_model=TokenPair)
def login(service: AuthSvc, payload: LoginRequest):
    return service.login(payload.email, payload.password)


@router.post("/refresh", response_model=TokenPair)
def refresh(service: AuthSvc, payload: TokenPair):
    return service.refresh(payload.refresh_token)


@router.post("/logout", status_code=204)
def logout(service: AuthSvc, payload: TokenPair):
    service.logout(payload.refresh_token)


@router.get("/me", response_model=User)
def me(user: CurrentUser):
    return user
