from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, load_settings
from app.db import connect
from app.repositories.tokens import TokenRepository
from app.repositories.users import UserRepository
from app.schemas import User
from app.services.auth import AuthService
from app.services.users import UserService

bearer = HTTPBearer(auto_error=False)


def get_settings() -> Settings:
    return load_settings()


def get_service(settings: Annotated[Settings, Depends(get_settings)]) -> UserService:
    """DI-фабрика: собирает цепочку Handler → Service → Repository → БД."""
    conn = connect(settings.database_path)
    return UserService(repo=UserRepository(conn))


def get_auth_service(settings: Annotated[Settings, Depends(get_settings)]) -> AuthService:
    conn = connect(settings.database_path)
    return AuthService(
        users=UserRepository(conn),
        tokens=TokenRepository(conn),
    )


Svc = Annotated[UserService, Depends(get_service)]
AuthSvc = Annotated[AuthService, Depends(get_auth_service)]
Creds = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]


def get_current_user(auth: AuthSvc, creds: Creds) -> User:
    if creds is None or creds.scheme.lower() != "bearer":
        from app.errors import UnauthorizedError

        raise UnauthorizedError("Отсутствует токен авторизации")
    return auth.get_current_user(creds.credentials)


CurrentUser = Annotated[User, Depends(get_current_user)]
