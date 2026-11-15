"""Dashboard SIGE — visual nativo do Streamlit.

Executar na raiz do projeto:
    streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

import data as D

st.set_page_config(
    page_title="SIGE — Dashboard de Vendas",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Esconde o menu lateral (não há conteúdo nele).
st.markdown(
    """
    <style>
        [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _fmt_moeda(valor: float) -> str:
    sinal = "-" if valor < 0 else ""
    v = abs(valor)
    if v >= 1_000_000_000:
        return f"{sinal}US$ {v / 1_000_000_000:.2f}B"
    if v >= 1_000_000:
        return f"{sinal}US$ {v / 1_000_000:.2f}M"
    if v >= 1_000:
        return f"{sinal}US$ {v / 1_000:.1f}K"
    return f"{sinal}US$ {v:,.0f}".replace(",", ".")


def _fmt_int(valor: float) -> str:
    return f"{int(valor):,}".replace(",", ".")


def _delta_pct(atual: float, anterior: float) -> str | None:
    if anterior in (0, None) or pd.isna(anterior):
        return None
    diff = (atual - anterior) / anterior * 100
    return f"{diff:+.1f}%"


# ---------------------------------------------------------------------------
# Barra de filtros — horizontal, acima dos totalizadores
# ---------------------------------------------------------------------------
def barra_filtros(df: pd.DataFrame) -> dict:
    data_min = df["data_pedido"].min().date()
    data_max = df["data_pedido"].max().date()

    c1, c2, c3, c4 = st.columns([1.4, 1, 1, 1])
    with c1:
        periodo = st.date_input(
            "Período",
            value=(data_min, data_max),
            min_value=data_min,
            max_value=data_max,
        )
        if not (isinstance(periodo, (tuple, list)) and len(periodo) == 2):
            periodo = (data_min, data_max)
    with c2:
        regioes = st.multiselect(
            "Região",
            sorted(df["regiao"].dropna().unique().tolist()),
            placeholder="Todas",
        )
    paises_opcoes = df if not regioes else df[df["regiao"].isin(regioes)]
    with c3:
        paises = st.multiselect(
            "País",
            sorted(paises_opcoes["pais"].dropna().unique().tolist()),
            placeholder="Todos",
        )
    with c4:
        modelos = st.multiselect(
            "Modelo",
            sorted(df["modelo"].dropna().unique().tolist()),
            placeholder="Todos",
        )

    with st.expander("Mais filtros", expanded=False):
        c5, c6, c7, c8 = st.columns(4)
        with c5:
            anos_modelo = st.multiselect(
                "Ano do modelo",
                sorted(df["ano_modelo"].dropna().unique().tolist(), reverse=True),
                placeholder="Todos",
            )
        with c6:
            generos = st.multiselect(
                "Gênero",
                sorted(df["genero"].dropna().unique().tolist()),
                placeholder="Todos",
            )
        with c7:
            escolaridades = st.multiselect(
                "Escolaridade",
                sorted(df["escolaridade"].dropna().unique().tolist()),
                placeholder="Todas",
            )
        with c8:
            idade_min = int(df["idade"].min())
            idade_max = int(df["idade"].max())
            faixa_idade = st.slider(
                "Faixa etária", idade_min, idade_max, (idade_min, idade_max),
            )

    return dict(
        periodo=periodo,
        regioes=regioes,
        paises=paises,
        modelos=modelos,
        anos_modelo=anos_modelo,
        generos=generos,
        escolaridades=escolaridades,
        faixa_idade=faixa_idade,
    )


# ---------------------------------------------------------------------------
# Deltas vs. janela anterior (mesma duração, deslocada para trás)
# ---------------------------------------------------------------------------
def _janela_anterior(df_total: pd.DataFrame, periodo, filtros_base: dict) -> pd.DataFrame:
    if not periodo or len(periodo) != 2:
        return df_total.iloc[0:0]
    inicio, fim = periodo
    delta = fim - inicio
    anterior_fim = inicio - pd.Timedelta(days=1)
    anterior_inicio = anterior_fim - delta
    return D.aplicar_filtros(
        df_total,
        **{
            **filtros_base,
            "periodo": (
                anterior_inicio.date() if hasattr(anterior_inicio, "date") else anterior_inicio,
                anterior_fim.date() if hasattr(anterior_fim, "date") else anterior_fim,
            ),
        },
    )


def _kpis_com_delta(df: pd.DataFrame, df_prev: pd.DataFrame) -> list[tuple[str, str, str | None]]:
    k = D.calcular_kpis(df)
    kp = D.calcular_kpis(df_prev)
    return [
        ("Faturamento", _fmt_moeda(k["faturamento"]), _delta_pct(k["faturamento"], kp["faturamento"])),
        ("Unidades vendidas", _fmt_int(k["unidades"]), _delta_pct(k["unidades"], kp["unidades"])),
        ("Modelo mais vendido", k["modelo_mais_vendido"], None),
        ("Região com maior receita", k["regiao_maior_receita"], None),
        ("Região com menor receita", k["regiao_menor_receita"], None),
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    try:
        df_total = D.carregar_dataset()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    if df_total.empty:
        st.warning("O banco está vazio — verifique a carga dos dados.")
        st.stop()

    st.title("Vendas de veículos")
    st.caption("Receita, performance regional e perfil dos clientes.")

    filtros = barra_filtros(df_total)
    df = D.aplicar_filtros(df_total, **filtros)
    df_prev = _janela_anterior(
        df_total, filtros["periodo"], {k: v for k, v in filtros.items() if k != "periodo"}
    )

    if df.empty:
        st.info("Sem resultados para os filtros atuais.")
        st.stop()

    st.divider()

    kpis = _kpis_com_delta(df, df_prev)
    cols = st.columns(3)
    for i, (label, value, delta) in enumerate(kpis):
        cols[i % len(cols)].metric(label, value, delta=delta)

    st.subheader("Receita no período")
    serie = D.serie_temporal(df, "W")
    fig = px.line(serie, x="data", y="receita", markers=True)
    fig.update_layout(height=320, margin=dict(l=8, r=8, t=28, b=8))
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Top 10 países")
        top = D.ranking(df, "pais", 10).sort_values("receita")
        fig = px.bar(top, x="receita", y="pais", orientation="h")
        fig.update_layout(height=340, margin=dict(l=8, r=8, t=28, b=8))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Top 10 modelos")
        top = D.ranking(df, "modelo", 10).sort_values("receita")
        fig = px.bar(top, x="receita", y="modelo", orientation="h")
        fig.update_layout(height=340, margin=dict(l=8, r=8, t=28, b=8))
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Receita por região")
        dist = D.distribuicao(df, "regiao")
        fig = px.bar(dist, x="regiao", y="receita")
        fig.update_layout(height=300, margin=dict(l=8, r=8, t=28, b=8))
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        st.subheader("Receita por faixa etária")
        fx = D.faixa_etaria(df)
        fig = px.bar(fx, x="faixa", y="receita")
        fig.update_layout(height=300, margin=dict(l=8, r=8, t=28, b=8))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Pedidos recentes")
    recentes = (
        df.sort_values("data_pedido", ascending=False)
        .head(15)[
            [
                "data_pedido", "cliente", "pais", "modelo", "quantidade",
                "receita_liquida", "avaliacao_cliente",
            ]
        ]
        .rename(
            columns={
                "data_pedido": "Data",
                "cliente": "Cliente",
                "pais": "País",
                "modelo": "Modelo",
                "quantidade": "Qtd",
                "receita_liquida": "Receita",
                "avaliacao_cliente": "Nota",
            }
        )
    )
    st.dataframe(
        recentes,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Receita": st.column_config.NumberColumn(format="$ %.0f"),
            "Nota": st.column_config.NumberColumn(format="%.2f"),
        },
    )


if __name__ == "__main__":
    main()
