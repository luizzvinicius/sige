"""API FastAPI que expõe os dados de produtos e vendas."""

import sqlite3
from contextlib import asynccontextmanager
from typing import Annotated, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from database.connection import get_connection, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Dashboard API", version="1.0.0", lifespan=lifespan)


class Produto(BaseModel):
    id: int
    nome: str
    valor: float


class VendaPorData(BaseModel):
    data: str
    valor_total: float


@app.get("/health", tags=["infra"])
def health() -> dict:
    """Healthcheck da API e da conexão com o banco."""
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=f"Banco indisponível: {exc}")

    return {"status": "ok", "database": "ok"}


@app.get("/produtos/{produto_id}", response_model=Produto, tags=["produtos"])
def buscar_produto(produto_id: int) -> Produto:
    """Busca um produto pelo id."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, nome, valor FROM produto WHERE id = ?", (produto_id,)
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    return Produto(**dict(row))


@app.get("/vendas", response_model=List[VendaPorData], tags=["vendas"])
def listar_vendas_por_data(
    data_inicio: Annotated[Optional[str], Query(description="AAAA-MM-DD")] = None,
    data_fim: Annotated[Optional[str], Query(description="AAAA-MM-DD")] = None,
) -> List[VendaPorData]:
    """Total vendido por dia, opcionalmente filtrado por período."""
    sql = "SELECT data_venda AS data, SUM(valor_total) AS valor_total FROM venda WHERE 1 = 1"
    params: list = []

    if data_inicio:
        sql += " AND data_venda >= ?"
        params.append(data_inicio)

    if data_fim:
        sql += " AND data_venda <= ?"
        params.append(data_fim)

    sql += " GROUP BY data_venda ORDER BY data_venda"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [VendaPorData(**dict(row)) for row in rows]
