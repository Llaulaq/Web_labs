import sqlite3


class AccountRepository:
    """Счета пользователей и денежные переводы."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get(self, user_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT user_id, balance FROM accounts WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None

    def create(self, user_id: int, balance: int = 0) -> dict:
        self.conn.execute(
            "INSERT INTO accounts (user_id, balance) VALUES (?, ?)", (user_id, balance)
        )
        self.conn.commit()
        return {"user_id": user_id, "balance": balance}

    def transfer(self, from_id: int, to_id: int, amount: int) -> None:
        """Атомарный перевод. Поднимает InsufficientFunds или AccountNotFound."""
        # IMMEDIATE захватывает блокировку БД до COMMIT — другие писатели ждут
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            row = self.conn.execute(
                "SELECT balance FROM accounts WHERE user_id = ?", (from_id,)
            ).fetchone()
            if row is None:
                raise AccountNotFound(from_id)
            if self.conn.execute(
                "SELECT 1 FROM accounts WHERE user_id = ?", (to_id,)
            ).fetchone() is None:
                raise AccountNotFound(to_id)
            # Атомарное списание: обновляется ровно одна строка, если средств хватает
            cursor = self.conn.execute(
                "UPDATE accounts SET balance = balance - ? WHERE user_id = ? AND balance >= ?",
                (amount, from_id, amount),
            )
            if cursor.rowcount == 0:
                raise InsufficientFunds()
            self.conn.execute(
                "UPDATE accounts SET balance = balance + ? WHERE user_id = ?",
                (amount, to_id),
            )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise


class InsufficientFunds(Exception):
    pass


class AccountNotFound(Exception):
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"Счёт пользователя {user_id} не найден")
