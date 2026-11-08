"""Conexão e inicialização do banco SQLite."""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "app.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"
DADOS_PATH = BASE_DIR / "commands.sql"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _split_transactions(sql: str) -> list[str]:
    """Separa comandos.sql nos blocos BEGIN/COMMIT gerados pelo conversor."""
    transactions = []
    current = []

    for line in sql.splitlines():
        statement = line.strip().upper()
        if statement == "BEGIN TRANSACTION;":
            if current:
                raise ValueError("Foi encontrado um BEGIN antes do COMMIT anterior.")
            current = [line]
        elif current:
            current.append(line)
            if statement == "COMMIT;":
                transactions.append("\n".join(current))
                current = []
        elif statement and not statement.startswith("--"):
            raise ValueError("Foi encontrado SQL fora de uma transacao.")

    if current:
        raise ValueError("Foi encontrada uma transacao sem COMMIT.")

    return transactions


def _execute_transactions(conn: sqlite3.Connection, sql: str) -> None:
    failures = []

    for number, transaction in enumerate(_split_transactions(sql), start=1):
        try:
            conn.executescript(transaction)
        except sqlite3.Error as error:
            conn.rollback()
            failures.append(f"transacao {number}: {error}")

    if failures:
        raise RuntimeError("Falha ao executar " + "; ".join(failures))


def init_db(force: bool = False) -> None:
    if DB_PATH.exists() and not force:
        return

    with get_connection() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _execute_transactions(conn, DADOS_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    init_db(force=True)
    print(f"Banco inicializado em {DB_PATH}")
