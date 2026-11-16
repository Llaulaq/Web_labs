from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.config import Settings
from app.db import connect
from app.deps import get_settings
from app.repositories.accounts import AccountRepository
from app.services.accounts import AccountService

router = APIRouter(prefix="/accounts", tags=["accounts"])


def get_account_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AccountService:
    conn = connect(settings.database_path)
    return AccountService(repo=AccountRepository(conn))


AcctSvc = Annotated[AccountService, Depends(get_account_service)]


class AccountCreate(BaseModel):
    user_id: int
    balance: int = Field(default=0, ge=0)


class TransferRequest(BaseModel):
    from_user_id: int
    to_user_id: int
    amount: int = Field(gt=0)


@router.get("/{user_id}")
def get_account(service: AcctSvc, user_id: int):
    return service.get(user_id)


@router.post("", status_code=201)
def create_account(service: AcctSvc, payload: AccountCreate):
    return service.create(payload.user_id, payload.balance)


@router.post("/transfer", status_code=204)
def transfer(service: AcctSvc, payload: TransferRequest):
    service.transfer(payload.from_user_id, payload.to_user_id, payload.amount)
