import logging

import jwt

from app.errors import AppError, UnauthorizedError
from app.repositories.tokens import TokenRepository
from app.repositories.users import UserRepository
from app.schemas import User
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_env_secret,
    verify_password,
)

logger = logging.getLogger("app")


class AuthService:
    """Аутентификация: выдача, обновление и отзыв JWT-токенов."""

    def __init__(self, users: UserRepository, tokens: TokenRepository):
        self.users = users
        self.tokens = tokens
        self.secret = get_env_secret()

    def login(self, email: str, password: str) -> dict:
        creds = self.users.get_credentials(email)
        if creds is None or not verify_password(password, creds[2]):
            logger.info("Неудачная попытка входа: %s", email)
            raise UnauthorizedError("Неверный email или пароль")
        user_id, user_email = creds[0], creds[1]
        logger.info("Успешный вход: id=%s", user_id)
        return self._issue_pair(user_id, user_email)

    def refresh(self, refresh_token: str) -> dict:
        payload = self._decode_active(refresh_token, kind="refresh")
        return self._issue_pair(int(payload["sub"]), payload["email"])

    def logout(self, refresh_token: str) -> None:
        payload = self._decode_active(refresh_token, kind="refresh")
        self.tokens.revoke(payload["jti"])
        logger.info("Выход пользователя id=%s: refresh-токен отозван", payload["sub"])

    def get_current_user(self, access_token: str) -> User:
        payload = self._decode_active(access_token, kind="access")
        user = self.users.get(int(payload["sub"]))
        if user is None:
            raise UnauthorizedError("Пользователь не существует")
        return user

    def _issue_pair(self, user_id: int, email: str) -> dict:
        return {
            "access_token": create_access_token(user_id, email, self.secret),
            "refresh_token": create_refresh_token(user_id, email, self.secret),
            "token_type": "bearer",
        }

    def _decode_active(self, token: str, kind: str) -> dict:
        try:
            payload = decode_token(token, self.secret)
        except jwt.PyJWTError:
            raise UnauthorizedError("Недействительный или просроченный токен")
        if payload.get("kind") != kind:
            raise UnauthorizedError("Неверный тип токена")
        if self.tokens.is_revoked(payload["jti"]):
            raise UnauthorizedError("Токен отозван")
        return payload
