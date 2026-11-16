from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    age: int | None = Field(default=None, ge=0, le=150)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    age: int | None = Field(default=None, ge=0, le=150)


class User(BaseModel):
    id: int
    name: str
    email: EmailStr
    age: int | None = None


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user


@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate):
    global _next_id
    if _email_taken(payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует",
        )
    user = User(id=_next_id, **payload.model_dump())
    _users[user.id] = user
    _next_id += 1
    return user


@router.put("/{user_id}", response_model=User)
def update_user(user_id: int, payload: UserUpdate):
    user = _users.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    data = payload.model_dump(exclude_unset=True)
    if "email" in data and _email_taken(data["email"], exclude_id=user_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует",
        )
    updated = user.model_copy(update=data)
    _users[user_id] = updated
    return updated


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int):
    if user_id not in _users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    del _users[user_id]
