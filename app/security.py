import base64
import hashlib
import hmac
import os
import secrets

import jwt
from datetime import datetime, timedelta, timezone

ALGORITHM = "HS256"
ACCESS_TOKEN_TTL = timedelta(minutes=15)
REFRESH_TOKEN_TTL = timedelta(days=7)


def hash_password(password: str) -> str:
    """PBKDF2-HMAC-SHA256 с солью: 'pbkdf2$<salt>$<hash>' (bcrypt-аналог, stdlib)."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return "pbkdf2${}${}".format(
        base64.b64encode(salt).decode(), base64.b64encode(digest).decode()
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt_b64, digest_b64 = stored.split("$")
    except ValueError:
        return False
    salt = base64.b64decode(salt_b64)
    expected = base64.b64decode(digest_b64)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return hmac.compare_digest(digest, expected)


def _create_token(user_id: int, email: str, kind: str, ttl: timedelta, secret: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "kind": kind,  # "access" | "refresh"
        "iat": now,
        "exp": now + ttl,
        "jti": secrets.token_hex(8),  # уникальный id токена для blacklist
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def create_access_token(user_id: int, email: str, secret: str) -> str:
    return _create_token(user_id, email, "access", ACCESS_TOKEN_TTL, secret)


def create_refresh_token(user_id: int, email: str, secret: str) -> str:
    return _create_token(user_id, email, "refresh", REFRESH_TOKEN_TTL, secret)


def decode_token(token: str, secret: str) -> dict:
    """Проверяет подпись и срок действия. Выбрасывает jwt.PyJWTError при ошибке."""
    return jwt.decode(token, secret, algorithms=[ALGORITHM])


def get_env_secret() -> str:
    """Секрет из окружения; для разработки — стабильный дефолт с предупреждением."""
    secret = os.getenv("SECRET_KEY")
    if not secret:
        secret = "dev-only-secret-change-me"
    return secret
