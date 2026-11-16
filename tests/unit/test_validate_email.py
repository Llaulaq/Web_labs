import pytest

from app.utils import validate_email


@pytest.mark.parametrize(
    "email, expected",
    [
        ("john@example.com", True),          # валидный email
        ("johnexample.com", False),          # без @
        ("jo@hn@example.com", False),        # несколько @
        ("@example.com", False),             # пустая локальная часть
        ("john@", False),                    # пустая доменная часть
        ("john@examplecom", False),          # домен без точки
    ],
)
def test_validate_email(email, expected):
    # Arrange — параметры подготовлены декоратором parametrize
    # Act
    result = validate_email(email)
    # Assert
    assert result is expected
