"""Dashboard Streamlit: total de vendas por data, com filtro de período."""

import os
from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Dashboard de Vendas", page_icon="📊", layout="wide")


@st.cache_data(ttl=60)
def buscar_vendas(data_inicio: date, data_fim: date) -> pd.DataFrame:
    """Consulta a API e devolve o total vendido por dia."""
    resposta = requests.get(
        f"{API_URL}/vendas",
        params={"data_inicio": data_inicio.isoformat(), "data_fim": data_fim.isoformat()},
        timeout=10,
    )
    resposta.raise_for_status()
    return pd.DataFrame(resposta.json(), columns=["data", "valor_total"])


st.title("Vendas por período")

hoje = date.today()

with st.sidebar:
    st.header("Filtros")
    periodo = st.date_input(
        "Período",
        value=(hoje - timedelta(days=30), hoje),
        max_value=hoje,
    )

if not isinstance(periodo, (tuple, list)) or len(periodo) != 2:
    st.info("Selecione a data inicial e a data final.")
    st.stop()

data_inicio, data_fim = periodo

if data_inicio > data_fim:
    st.error("A data inicial não pode ser maior que a data final.")
    st.stop()

try:
    df = buscar_vendas(data_inicio, data_fim)
except requests.RequestException as exc:
    st.error(f"Não foi possível consultar a API ({API_URL}): {exc}")
    st.stop()

if df.empty:
    st.info("Nenhuma venda encontrada no período selecionado.")
    st.stop()

df["data"] = pd.to_datetime(df["data"])

st.bar_chart(df, x="data", y="valor_total", x_label="Data", y_label="Valor da venda (R$)")
