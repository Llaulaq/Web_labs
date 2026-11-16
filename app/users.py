import logging
import re

from fastapi import APIRouter, Query
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.errors import ConflictError, NotFoundError

logger = logging.getLogger("app")
router = APIRouter(prefix="/users", tags=["users"])

NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁё\s\-]+$")
PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).+$")


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    age: int = Field(ge=18, le=120)
    password: str = Field(min_length=8, max_length=128, exclude=True)

    @field_validator("name")
    @classmethod
    def name_only_letters(cls, value: str) -> str:
        if not NAME_RE.match(value):
            raise ValueError("Имя должно содержать только буквы, пробелы и дефисы")
        return value

    @field_validator("password")
    @classmethod
    def password_strong(cls, value: str) -> str:
        if not PASSWORD_RE.match(value):
            raise ValueError("Пароль должен содержать буквы и цифры")
        return value


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    email: EmailStr | None = None
    age: int | None = Field(default=None, ge=18, le=120)

    @field_validator("name")
    @classmethod
    def name_only_letters(cls, value: str | None) -> str | None:
        if value is not None and not NAME_RE.match(value):
            raise ValueError("Имя должно содержать только буквы, пробелы и дефисы")
        return value


class User(BaseModel):
    id: int
    name: str
    email: EmailStr
    age: int


class UserList(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[User]


# Хранилище в памяти (в лабораторной 4 заменяется на базу данных)
_users: dict[int, User] = {}
_next_id: int = 1


def _email_taken(email: str, exclude_id: int | None = None) -> bool:
    return any(u.email == email and u.id != exclude_id for u in _users.values())


@router.get("", response_model=UserList)
def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    search: str | None = Query(default=None, max_length=100),
):
    items = list(_users.values())
    if search:
        needle = search.lower()
        items = [u for u in items if needle in u.name.lower() or needle in u.email.lower()]
    total = len(items)
    return UserList(total=total, skip=skip, limit=limit, items=items[skip : skip + limit])


@router.get("/{user_id}", response_model=User)
def get_user(user_id: int):
    user = _users.get(user_id)
    if user is None:
        raise NotFoundError("Пользователь не найден")
    return user


@router.post("", response_model=User, status_code=201)
def create_user(payload: UserCreate):
    global _next_id
    if _email_taken(payload.email):
        logger.info("Отказ в создании: email занят: %s", payload.email)
        raise ConflictError("Пользователь с таким email уже существует", {"email": "already_taken"})
    user = User(id=_next_id, name=payload.name, email=payload.email, age=payload.age)
    _users[user.id] = user
    _next_id += 1
    logger.info("Создан пользователь id=%s email=%s", user.id, user.email)
    return user


@router.put("/{user_id}", response_model=User)
def update_user(user_id: int, payload: UserUpdate):
    user = _users.get(user_id)
    if user is None:
        raise NotFoundError("Пользователь не найден")
    data = payload.model_dump(exclude_unset=True)
    if "email" in data and _email_taken(data["email"], exclude_id=user_id):
        raise ConflictError("Пользователь с таким email уже существует", {"email": "already_taken"})
    updated = user.model_copy(update=data)
    _users[user_id] = updated
    logger.info("Обновлён пользователь id=%s", user_id)
    return updated


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int):
    if user_id not in _users:
        raise NotFoundError("Пользователь не найден")
    del _users[user_id]
    logger.info("Удалён пользователь id=%s", user_id)
