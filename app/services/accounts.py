import logging

from app.errors import AppError, NotFoundError
from app.repositories.accounts import AccountNotFound, AccountRepository, InsufficientFunds

logger = logging.getLogger("app")


class AccountService:
    def __init__(self, repo: AccountRepository):
        self.repo = repo

    def get(self, user_id: int) -> dict:
        account = self.repo.get(user_id)
        if account is None:
            raise NotFoundError("Счёт не найден")
        return account

    def create(self, user_id: int, balance: int = 0) -> dict:
        if balance < 0:
            raise AppError("validation_error", "Начальный баланс не может быть отрицательным", 422)
        try:
            return self.repo.create(user_id, balance)
        except Exception as exc:  # UNIQUE(user_id): счёт уже существует
            if "UNIQUE" in str(exc):
                raise AppError("conflict", "Счёт для этого пользователя уже существует", 409)
            raise

    def transfer(self, from_id: int, to_id: int, amount: int) -> None:
        if from_id == to_id:
            raise AppError("validation_error", "Нельзя перевести деньги самому себе", 422)
        if amount <= 0:
            raise AppError("validation_error", "Сумма перевода должна быть положительной", 422)
        try:
            self.repo.transfer(from_id, to_id, amount)
        except InsufficientFunds:
            raise AppError("insufficient_funds", "Недостаточно средств на счёте", 422)
        except AccountNotFound as exc:
            raise NotFoundError(str(exc))
        logger.info("Перевод %s → %s: %s", from_id, to_id, amount)
