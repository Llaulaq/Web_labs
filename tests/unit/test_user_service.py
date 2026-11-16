from unittest.mock import Mock

import pytest

from app.errors import ConflictError, NotFoundError
from app.schemas import UserCreate
from app.services.users import UserService

VALID = {"name": "John Doe", "email": "john@example.com", "age": 30, "password": "pass12345"}


def make_service():
    # Arrange: сервис с моком репозитория
    repo = Mock()
    return UserService(repo=repo), repo


def test_create_success():
    service, repo = make_service()
    repo.get_by_email.return_value = None
    repo.create.return_value = Mock(id=1, name="John Doe", email="john@example.com", age=30)

    # Act
    user = service.create(UserCreate(**VALID))

    # Assert: возвращённый пользователь и вызовы мока
    assert user.id == 1
    assert user.email == "john@example.com"
    repo.get_by_email.assert_called_once_with("john@example.com")
    repo.create.assert_called_once()


def test_create_duplicate_email_raises_conflict():
    service, repo = make_service()
    repo.get_by_email.return_value = Mock(id=99)  # email уже занят

    with pytest.raises(ConflictError):
        service.create(UserCreate(**VALID))

    repo.create.assert_not_called()  # сохранение не выполнялось


def test_get_raises_not_found_when_missing():
    service, repo = make_service()
    repo.get.return_value = None

    with pytest.raises(NotFoundError):
        service.get(123)

    repo.get.assert_called_once_with(123)


def test_get_returns_user():
    service, repo = make_service()
    repo.get.return_value = Mock(id=1, name="John", email="j@example.com", age=30)

    user = service.get(1)

    assert user.id == 1


def test_update_checks_email_uniqueness_only_when_changed():
    service, repo = make_service()
    repo.get.return_value = Mock(id=1, name="John", email="old@example.com", age=30)
    repo.get_by_email.return_value = Mock(id=2)  # чужой email
    payload = Mock()
    payload.email = "taken@example.com"
    payload.model_dump = lambda exclude_unset: {"email": "taken@example.com"}

    with pytest.raises(ConflictError):
        service.update(1, payload)


def test_delete_raises_not_found():
    service, repo = make_service()
    repo.delete.return_value = False

    with pytest.raises(NotFoundError):
        service.delete(42)
