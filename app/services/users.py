import logging
import sqlite3

from app.errors import ConflictError, NotFoundError
from app.repositories.users import UserRepository
from app.schemas import User, UserCreate, UserUpdate

logger = logging.getLogger("app")


class UserService:
    """Бизнес-логика пользователей. Зависит от репозитория (DI), не знает про HTTP."""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def list(self, skip: int, limit: int, search: str | None) -> tuple[int, list[User]]:
        return self.repo.list(skip=skip, limit=limit, search=search)

    def get(self, user_id: int) -> User:
        user = self.repo.get(user_id)
        if user is None:
            raise NotFoundError("Пользователь не найден")
        return user

    def create(self, payload: UserCreate) -> User:
        if self.repo.get_by_email(payload.email):
            logger.info("Отказ в создании: email занят: %s", payload.email)
            raise ConflictError(
                "Пользователь с таким email уже существует", {"email": "already_taken"}
            )
        try:
            user = self.repo.create(payload)
        except sqlite3.IntegrityError:
            # Защита от гонки: UNIQUE-ограничение БД сработало одновременной проверки
            raise ConflictError(
                "Пользователь с таким email уже существует", {"email": "already_taken"}
            )
        logger.info("Создан пользователь id=%s email=%s", user.id, user.email)
        return user

    def update(self, user_id: int, payload: UserUpdate) -> User:
        existing = self.get(user_id)
        if payload.email and payload.email != existing.email:
            if self.repo.get_by_email(payload.email):
                raise ConflictError(
                    "Пользователь с таким email уже существует", {"email": "already_taken"}
                )
        updated = self.repo.update(user_id, payload)
        if updated is None:
            raise NotFoundError("Пользователь не найден")
        logger.info("Обновлён пользователь id=%s", user_id)
        return updated

    def delete(self, user_id: int) -> None:
        if not self.repo.delete(user_id):
            raise NotFoundError("Пользователь не найден")
        logger.info("Удалён пользователь id=%s", user_id)
