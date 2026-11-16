from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.deps import Svc
from app.schemas import User, UserCreate, UserList, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserList)
def list_users(
    service: Svc,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    search: str | None = Query(default=None, max_length=100),
):
    total, items = service.list(skip=skip, limit=limit, search=search)
    return UserList(total=total, skip=skip, limit=limit, items=items)


@router.get("/{user_id}", response_model=User)
def get_user(service: Svc, user_id: int):
    return service.get(user_id)


@router.post("", response_model=User, status_code=201)
def create_user(service: Svc, payload: UserCreate):
    return service.create(payload)


@router.put("/{user_id}", response_model=User)
def update_user(service: Svc, user_id: int, payload: UserUpdate):
    return service.update(user_id, payload)


@router.delete("/{user_id}", status_code=204)
def delete_user(service: Svc, user_id: int):
    service.delete(user_id)
