"""Camada de acesso a dados do dashboard.

Consulta o SQLite diretamente — o arquivo do banco é gerado por
``executar.bat`` (ou manualmente com ``python -m database.connection``).
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "app.db"


def _connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Banco de dados não encontrado em {DB_PATH}. "
            "Rode `executar.bat` ou `python -m database.connection` para criá-lo."
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@st.cache_data(ttl=300, show_spinner=False)
def carregar_dataset() -> pd.DataFrame:
    """Dataset desnormalizado — uma linha por item de pedido."""
    sql = """
        SELECT
            p.id_pedido,
            p.data_pedido,
            p.total               AS total_pedido,
            p.avaliacao_cliente,
            pais.nome             AS pais,
            r.nome                AS regiao,
            cli.id_cliente,
            cli.nome              AS cliente,
            cli.idade,
            cli.genero,
            cli.escolaridade,
            cli.cidade,
            car.id_carro,
            car.modelo,
            car.ano               AS ano_modelo,
            it.quantidade,
            it.preco_item,
            it.desconto,
            (it.preco_item * it.quantidade) - it.desconto AS receita_liquida
        FROM pedido       p
        JOIN item_pedido  it  ON it.id_pedido = p.id_pedido
        JOIN carro        car ON car.id_carro = it.id_carro
        JOIN pais         pais ON pais.id_pais = p.id_pais
        JOIN regiao       r    ON r.id_regiao = pais.id_regiao
        JOIN cliente      cli  ON cli.id_cliente = p.id_cliente
    """
    with _connect() as conn:
        df = pd.read_sql_query(sql, conn)

    df["data_pedido"] = pd.to_datetime(df["data_pedido"], errors="coerce")
    df = df.dropna(subset=["data_pedido"])
    df["ano"] = df["data_pedido"].dt.year
    df["mes"] = df["data_pedido"].dt.to_period("M").dt.to_timestamp()
    df["taxa_desconto"] = (df["desconto"] / df["preco_item"]).clip(lower=0, upper=1)
    return df


def aplicar_filtros(
    df: pd.DataFrame,
    *,
    periodo: tuple[date, date] | None = None,
    regioes: list[str] | None = None,
    paises: list[str] | None = None,
    modelos: list[str] | None = None,
    anos_modelo: list[int] | None = None,
    generos: list[str] | None = None,
    escolaridades: list[str] | None = None,
    faixa_idade: tuple[int, int] | None = None,
) -> pd.DataFrame:
    filtrado = df
    if periodo and len(periodo) == 2 and all(periodo):
        inicio, fim = periodo
        filtrado = filtrado[
            (filtrado["data_pedido"].dt.date >= inicio)
            & (filtrado["data_pedido"].dt.date <= fim)
        ]
    if regioes:
        filtrado = filtrado[filtrado["regiao"].isin(regioes)]
    if paises:
        filtrado = filtrado[filtrado["pais"].isin(paises)]
    if modelos:
        filtrado = filtrado[filtrado["modelo"].isin(modelos)]
    if anos_modelo:
        filtrado = filtrado[filtrado["ano_modelo"].isin(anos_modelo)]
    if generos:
        filtrado = filtrado[filtrado["genero"].isin(generos)]
    if escolaridades:
        filtrado = filtrado[filtrado["escolaridade"].isin(escolaridades)]
    if faixa_idade:
        idade_min, idade_max = faixa_idade
        filtrado = filtrado[
            (filtrado["idade"] >= idade_min) & (filtrado["idade"] <= idade_max)
        ]
    return filtrado


def calcular_kpis(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "receita": 0.0,
            "pedidos": 0,
            "clientes": 0,
            "ticket_medio": 0.0,
            "avaliacao": 0.0,
            "desconto_medio": 0.0,
            "unidades": 0,
        }
    return {
        "receita": float(df["receita_liquida"].sum()),
        "pedidos": int(df["id_pedido"].nunique()),
        "clientes": int(df["id_cliente"].nunique()),
        "ticket_medio": float(df.groupby("id_pedido")["total_pedido"].first().mean()),
        "avaliacao": float(df["avaliacao_cliente"].dropna().mean() or 0),
        "desconto_medio": float(df["taxa_desconto"].mean() * 100),
        "unidades": int(df["quantidade"].sum()),
    }


def serie_temporal(df: pd.DataFrame, granularidade: str = "D") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["data", "receita", "pedidos"])
    chave = df["data_pedido"].dt.to_period(granularidade).dt.to_timestamp()
    agg = df.groupby(chave).agg(
        receita=("receita_liquida", "sum"),
        pedidos=("id_pedido", "nunique"),
    ).reset_index(names="data")
    return agg


def ranking(df: pd.DataFrame, coluna: str, n: int = 10) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[coluna, "receita", "pedidos"])
    return (
        df.groupby(coluna)
        .agg(receita=("receita_liquida", "sum"), pedidos=("id_pedido", "nunique"))
        .sort_values("receita", ascending=False)
        .head(n)
        .reset_index()
    )


def distribuicao(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[coluna, "receita"])
    return (
        df.groupby(coluna)["receita_liquida"]
        .sum()
        .reset_index(name="receita")
        .sort_values("receita", ascending=False)
    )


def faixa_etaria(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["faixa", "receita", "clientes"])
    bins = [0, 24, 34, 44, 54, 64, 150]
    labels = ["<25", "25-34", "35-44", "45-54", "55-64", "65+"]
    faixas = pd.cut(df["idade"], bins=bins, labels=labels, right=True)
    return (
        df.assign(faixa=faixas)
        .groupby("faixa", observed=True)
        .agg(receita=("receita_liquida", "sum"), clientes=("id_cliente", "nunique"))
        .reset_index()
    )
