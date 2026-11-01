"""Conexão e inicialização do banco SQLite."""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "app.db"
SCHEMA_PATH = BASE_DIR / "init.sql"


def get_connection() -> sqlite3.Connection:
    """Abre uma conexão com o banco, com acesso por nome de coluna e FKs ativas."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(force: bool = False) -> None:
    """Executa a migration de carga (database/init.sql).

    Se o banco já existir e force=False, nada é feito.
    """
    if DB_PATH.exists() and not force:
        return

    with get_connection() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    init_db(force=True)
    print(f"Banco inicializado em {DB_PATH}")
