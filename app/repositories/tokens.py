import sqlite3


class TokenRepository:
    """Хранилище отозванных токенов (blacklist) в БД."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def revoke(self, jti: str) -> None:
        self.conn.execute("INSERT OR IGNORE INTO revoked_tokens (jti) VALUES (?)", (jti,))
        self.conn.commit()

    def is_revoked(self, jti: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM revoked_tokens WHERE jti = ?", (jti,)
        ).fetchone()
        return row is not None
