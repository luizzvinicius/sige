"""API FastAPI que expõe o dataset de vendas de veículos já filtrado."""

import sqlite3
from contextlib import asynccontextmanager
from datetime import date
from typing import Annotated, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from database.connection import get_connection, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Dashboard API", version="1.0.0", lifespan=lifespan)


class DadoVenda(BaseModel):
    """Uma linha do dataset (item de pedido) com os filtros aplicados."""

    id_pedido: str
    data_pedido: date
    total_pedido: float
    avaliacao_cliente: Optional[float]
    regiao: str
    pais: str
    cliente: str
    idade: Optional[int]
    genero: Optional[str]
    escolaridade: Optional[str]
    cidade: Optional[str]
    modelo: str
    ano_modelo: int
    quantidade: int
    preco_item: float
    desconto: float
    faturamento: float
    receita_liquida: float


class RespostaDados(BaseModel):
    total_registros: int
    dados: List[DadoVenda]


_QUERY_DADOS = """
    SELECT
        p.id_pedido,
        p.data_pedido,
        p.total               AS total_pedido,
        p.avaliacao_cliente,
        r.nome                AS regiao,
        pais.nome             AS pais,
        cli.nome              AS cliente,
        cli.idade,
        cli.genero,
        cli.escolaridade,
        cli.cidade,
        car.modelo,
        car.ano               AS ano_modelo,
        it.quantidade,
        it.preco_item,
        it.desconto,
        (it.preco_item * it.quantidade)               AS faturamento,
        (it.preco_item * it.quantidade) - it.desconto AS receita_liquida
    FROM pedido       p
    JOIN item_pedido  it   ON it.id_pedido = p.id_pedido
    JOIN carro        car  ON car.id_carro = it.id_carro
    JOIN pais         pais ON pais.id_pais = p.id_pais
    JOIN regiao       r    ON r.id_regiao = pais.id_regiao
    JOIN cliente      cli  ON cli.id_cliente = p.id_cliente
    WHERE 1 = 1
"""


@app.get("/health", tags=["infra"])
def health() -> dict:
    """Healthcheck da API e da conexão com o banco."""
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=503, detail=f"Banco indisponível: {exc}"
        ) from exc

    return {"status": "ok", "database": "ok"}


def _carregar_referencia(conn: sqlite3.Connection) -> dict:
    """Carrega os valores válidos e os limites de referência usados na validação."""
    datas_min, datas_max = conn.execute(
        "SELECT MIN(data_pedido), MAX(data_pedido) FROM pedido"
    ).fetchone()
    idade_min, idade_max = conn.execute(
        "SELECT MIN(idade), MAX(idade) FROM cliente"
    ).fetchone()

    def valores(sql: str) -> set:
        return {row[0] for row in conn.execute(sql)}

    return {
        "data_min": date.fromisoformat(datas_min),
        "data_max": date.fromisoformat(datas_max),
        "idade_min": idade_min,
        "idade_max": idade_max,
        "regioes": valores("SELECT nome FROM regiao"),
        "paises": valores("SELECT nome FROM pais"),
        "regiao_do_pais": dict(
            conn.execute(
                "SELECT p.nome, r.nome FROM pais p JOIN regiao r ON r.id_regiao = p.id_regiao"
            )
        ),
        "modelos": valores("SELECT DISTINCT modelo FROM carro"),
        "anos": valores("SELECT DISTINCT ano FROM carro"),
        "generos": valores("SELECT DISTINCT genero FROM cliente"),
        "escolaridades": valores("SELECT DISTINCT escolaridade FROM cliente"),
    }


def _validar_opcoes(rotulo: str, valores: Optional[List], aceitos: set) -> list:
    """Garante que todos os valores informados existem no banco."""
    if not valores:
        return []

    invalidos = sorted({valor for valor in valores if valor not in aceitos})
    if invalidos:
        raise HTTPException(
            status_code=422,
            detail=(
                f"{rotulo} inválido: {', '.join(str(v) for v in invalidos)}. "
                f"Valores aceitos: {', '.join(str(v) for v in sorted(aceitos))}."
            ),
        )
    return valores


def _validar_filtros(filtros: dict, referencia: dict) -> None:
    """Valida os filtros informados contra os dados disponíveis no banco."""
    data_min, data_max = referencia["data_min"], referencia["data_max"]
    periodo = f"{data_min:%d/%m/%Y} a {data_max:%d/%m/%Y}"

    for chave, rotulo in (("data_inicio", "Data inicial"), ("data_fim", "Data final")):
        valor = filtros[chave]
        if valor is not None and not data_min <= valor <= data_max:
            raise HTTPException(
                status_code=422,
                detail=f"{rotulo} fora do período de referência ({periodo}).",
            )

    if filtros["data_inicio"] and filtros["data_fim"]:
        if filtros["data_inicio"] > filtros["data_fim"]:
            raise HTTPException(
                status_code=422,
                detail="Data inicial não pode ser posterior à data final.",
            )

    filtros["regiao"] = _validar_opcoes("Região", filtros["regiao"], referencia["regioes"])
    filtros["pais"] = _validar_opcoes("País", filtros["pais"], referencia["paises"])
    filtros["modelo"] = _validar_opcoes("Modelo", filtros["modelo"], referencia["modelos"])
    filtros["ano"] = _validar_opcoes("Ano do veículo", filtros["ano"], referencia["anos"])
    filtros["genero"] = _validar_opcoes("Gênero", filtros["genero"], referencia["generos"])
    filtros["escolaridade"] = _validar_opcoes(
        "Escolaridade", filtros["escolaridade"], referencia["escolaridades"]
    )

    regiao_do_pais = referencia["regiao_do_pais"]
    for nome in filtros["pais"]:
        regiao = regiao_do_pais[nome]
        if filtros["regiao"] and regiao not in filtros["regiao"]:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"O país {nome} pertence à região {regiao} e não pode ser combinado "
                    f"com as regiões selecionadas: {', '.join(filtros['regiao'])}."
                ),
            )

    idade_min, idade_max = referencia["idade_min"], referencia["idade_max"]
    for chave, rotulo in (("idade_min", "Idade mínima"), ("idade_max", "Idade máxima")):
        valor = filtros[chave]
        if valor is not None and not idade_min <= valor <= idade_max:
            raise HTTPException(
                status_code=422,
                detail=f"{rotulo} deve estar entre {idade_min} e {idade_max} anos.",
            )

    if filtros["idade_min"] is not None and filtros["idade_max"] is not None:
        if filtros["idade_min"] > filtros["idade_max"]:
            raise HTTPException(
                status_code=422,
                detail="Idade mínima não pode ser maior que a idade máxima.",
            )


def _filtro_in(coluna: str, valores: Optional[List]) -> tuple[str, list]:
    """Monta um trecho `IN (?, ?, ...)` mantendo os valores como bind."""
    if not valores:
        return "", []
    placeholders = ", ".join("?" for _ in valores)
    return f" AND {coluna} IN ({placeholders})", list(valores)


def _montar_consulta(filtros: dict) -> tuple[str, list]:
    """Monta a query com bind de parâmetros (nunca interpola valores no SQL)."""
    sql = _QUERY_DADOS
    params: list = []

    if filtros["data_inicio"]:
        sql += " AND p.data_pedido >= ?"
        params.append(filtros["data_inicio"].isoformat())

    if filtros["data_fim"]:
        sql += " AND p.data_pedido <= ?"
        params.append(filtros["data_fim"].isoformat())

    for coluna, valores in (
        ("r.nome", filtros["regiao"]),
        ("pais.nome", filtros["pais"]),
        ("car.modelo", filtros["modelo"]),
        ("car.ano", filtros["ano"]),
        ("cli.genero", filtros["genero"]),
        ("cli.escolaridade", filtros["escolaridade"]),
    ):
        clausula, valores_bind = _filtro_in(coluna, valores)
        sql += clausula
        params.extend(valores_bind)

    if filtros["idade_min"] is not None:
        sql += " AND cli.idade >= ?"
        params.append(filtros["idade_min"])

    if filtros["idade_max"] is not None:
        sql += " AND cli.idade <= ?"
        params.append(filtros["idade_max"])

    sql += " ORDER BY p.data_pedido, p.id_pedido"
    return sql, params


@app.get("/api/dados", response_model=RespostaDados, tags=["dados"])
def obter_dados(
    data_inicio: Annotated[Optional[date], Query(description="Início do período (AAAA-MM-DD)")] = None,
    data_fim: Annotated[Optional[date], Query(description="Fim do período (AAAA-MM-DD)")] = None,
    regiao: Annotated[Optional[List[str]], Query(description="Região (parâmetro pode se repetir)")] = None,
    pais: Annotated[Optional[List[str]], Query(description="País (deve pertencer à região informada)")] = None,
    modelo: Annotated[Optional[List[str]], Query(description="Modelo do veículo")] = None,
    ano: Annotated[Optional[List[int]], Query(description="Ano do modelo do veículo")] = None,
    genero: Annotated[Optional[List[str]], Query(description="Gênero do cliente")] = None,
    escolaridade: Annotated[Optional[List[str]], Query(description="Escolaridade do cliente")] = None,
    idade_min: Annotated[Optional[int], Query(description="Idade mínima do cliente")] = None,
    idade_max: Annotated[Optional[int], Query(description="Idade máxima do cliente")] = None,
) -> RespostaDados:
    """Retorna os itens de pedido (uma linha por veículo vendido) com os filtros do dashboard.

    Todos os parâmetros são opcionais; sem filtros, retorna o dataset completo.
    """
    filtros = {
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "regiao": regiao,
        "pais": pais,
        "modelo": modelo,
        "ano": ano,
        "genero": genero,
        "escolaridade": escolaridade,
        "idade_min": idade_min,
        "idade_max": idade_max,
    }

    with get_connection() as conn:
        referencia = _carregar_referencia(conn)
        _validar_filtros(filtros, referencia)
        sql, params = _montar_consulta(filtros)
        rows = conn.execute(sql, params).fetchall()

    dados = [DadoVenda(**dict(row)) for row in rows]
    return RespostaDados(total_registros=len(dados), dados=dados)
