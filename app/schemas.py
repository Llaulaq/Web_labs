import re

from pydantic import BaseModel, EmailStr, Field, field_validator

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
