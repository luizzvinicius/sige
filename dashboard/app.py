"""Dashboard SIGE — gráficos em Apache ECharts (streamlit-echarts).

Executar na raiz do projeto:
    streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_echarts import JsCode, st_echarts

sys.path.insert(0, str(Path(__file__).resolve().parent))

import data as D

st.set_page_config(
    page_title="SIGE — Dashboard de Vendas",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilo claro inspirado em dashboards analíticos, mantendo a sidebar recolhível.
st.markdown(
    """
    <style>
        .stApp {
            background: #F7F9FC;
        }
        [data-testid="stSidebar"] {
            background: #172438;
        }
        [data-testid="stSidebar"] * {
            color: #E8EEF8;
        }
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] [data-baseweb="select"] > div {
            color: #172033;
        }
        [data-testid="stSidebar"] input {
            -webkit-text-fill-color: #172033;
        }
        [data-testid="stSidebar"] [data-testid="stDateInputFieldsScroller"] span {
            color: #172033 !important;
            -webkit-text-fill-color: #172033;
            opacity: 1;
        }
        [data-testid="stSidebar"] [data-testid="stExpander"] {
            border: 1px solid rgba(226, 232, 240, 0.2);
            border-radius: 10px;
            background: #1E2E44;
        }
        [data-testid="stSidebar"] [data-testid="stExpander"] summary {
            padding: 0.65rem 0.9rem;
            color: #F1F5F9;
            background: #1E2E44;
        }
        [data-testid="stSidebar"] [data-testid="stExpanderDetails"] {
            padding: 0.6rem 1rem 0.9rem;
        }
        [data-testid="stSidebar"] [data-testid="stExpander"] button {
            color: #52637A;
        }
        [data-testid="stSidebar"] button[aria-label="Open"] {
            color: #52637A;
            background: transparent;
            border-radius: 0 8px 8px 0;
        }
        [data-testid="stSidebar"] button[aria-label="Open"] svg,
        [data-testid="stSidebar"] [data-testid="stDateInputCalendarButton"] svg {
            color: #52637A !important;
            fill: #52637A !important;
        }
        [data-testid="stSidebar"] button[aria-label="Open"]:hover {
            background: #E9EFF7;
        }
        [data-testid="stSidebar"] [data-testid="stDateInputCalendarButton"] {
            color: #52637A;
            background: transparent;
            border-radius: 8px;
        }
        [data-testid="stSidebar"] [data-testid="stDateInputCalendarButton"]:hover {
            background: #E9EFF7;
        }
        [data-testid="stMetric"] {
            padding: 16px 18px;
            background: #FFFFFF;
            border: 1px solid #E7ECF3;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(23, 36, 56, 0.04);
        }
        [data-testid="stMetricValue"] {
            font-size: 1.25rem;
            white-space: normal;
        }
        [data-testid="stMetricLabel"] {
            color: #64748B;
        }
        h1, h2, h3 {
            letter-spacing: -0.025em;
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: #AFC0D8;
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
# Opções ECharts
# ---------------------------------------------------------------------------
_CORES_GRAFICOS = [
    "#3B82F6",
    "#14B8A6",
    "#F59E0B",
    "#8B5CF6",
    "#F97316",
    "#EC4899",
    "#22C55E",
    "#06B6D4",
    "#EF4444",
    "#A855F7",
]


def _formatter_moeda() -> JsCode:
    """Abrevia valores monetários em tooltips e eixos."""
    return JsCode(
        "function (value) {"
        " var v = Number(value), a = Math.abs(v);"
        " if (a >= 1e9) return 'US$ ' + (v / 1e9).toFixed(2) + 'B';"
        " if (a >= 1e6) return 'US$ ' + (v / 1e6).toFixed(2) + 'M';"
        " if (a >= 1e3) return 'US$ ' + (v / 1e3).toFixed(1) + 'K';"
        " return 'US$ ' + v.toFixed(0);"
        "}"
    )


def _formatter_linha() -> JsCode:
    """Formata as unidades de cada série sem misturar pedidos e receita."""
    return JsCode(
        "function (params) {"
        " return params.map(function (p) {"
        "  var value = Number(p.value);"
        "  var label = p.seriesName === 'Receita'"
        "   ? 'US$ ' + value.toLocaleString('pt-BR', {maximumFractionDigits: 0})"
        "   : value.toLocaleString('pt-BR') + ' pedidos';"
        "  return p.marker + ' ' + p.seriesName + ': ' + label;"
        " }).join('<br/>');"
        "}"
    )


def _opcoes_linha(serie: pd.DataFrame) -> dict:
    """Série temporal interativa de receita e pedidos."""
    return {
        "color": _CORES_GRAFICOS,
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"},
            "formatter": _formatter_linha(),
        },
        "legend": {"top": 8, "left": 12},
        "toolbox": {
            "right": 8,
            "feature": {
                "dataZoom": {"yAxisIndex": "none"},
                "restore": {},
                "saveAsImage": {"pixelRatio": 2},
            },
        },
        "grid": {"left": 12, "right": 48, "top": 52, "bottom": 48, "containLabel": True},
        "xAxis": {
            "type": "category",
            "boundaryGap": False,
            "data": serie["data"].dt.strftime("%d/%m/%Y").tolist(),
        },
        "yAxis": [
            {"type": "value", "axisLabel": {"formatter": _formatter_moeda()}},
            {"type": "value", "position": "right", "minInterval": 1},
        ],
        "dataZoom": [
            {"type": "inside", "xAxisIndex": 0},
            {"type": "slider", "xAxisIndex": 0, "height": 18, "bottom": 8},
        ],
        "series": [
            {
                "name": "Receita",
                "type": "line",
                "yAxisIndex": 0,
                "smooth": True,
                "showSymbol": False,
                "symbolSize": 8,
                "lineStyle": {"width": 3},
                "areaStyle": {
                    "opacity": 0.2,
                    "color": {
                        "type": "linear",
                        "x": 0,
                        "y": 0,
                        "x2": 0,
                        "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "rgba(59, 130, 246, 0.42)"},
                            {"offset": 1, "color": "rgba(59, 130, 246, 0.02)"},
                        ],
                    },
                },
                "data": [round(float(v), 2) for v in serie["receita"]],
            },
            {
                "name": "Pedidos",
                "type": "line",
                "yAxisIndex": 1,
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"width": 2, "type": "dashed"},
                "data": [int(v) for v in serie["pedidos"]],
            },
        ],
    }


def _opcoes_barras(categorias, valores, *, horizontal: bool) -> dict:
    """Opções ECharts para barras verticais ou horizontais de receita."""
    eixo_categoria = {
        "type": "category",
        "data": [str(c) for c in categorias],
        "inverse": horizontal,
    }
    eixo_valor = {"type": "value", "axisLabel": {"formatter": _formatter_moeda()}}
    eixo_x, eixo_y = (eixo_valor, eixo_categoria) if horizontal else (eixo_categoria, eixo_valor)
    return {
        "color": _CORES_GRAFICOS,
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "valueFormatter": _formatter_moeda(),
        },
        "toolbox": {
            "right": 8,
            "feature": {
                "dataZoom": {"yAxisIndex": "none"} if horizontal else {"xAxisIndex": "none"},
                "magicType": {"type": ["line", "bar"]},
                "restore": {},
                "saveAsImage": {"pixelRatio": 2},
            },
        },
        "grid": {"left": 12, "right": 28, "top": 42, "bottom": 16, "containLabel": True},
        "xAxis": eixo_x,
        "yAxis": eixo_y,
        "dataZoom": [
            {"type": "inside", "yAxisIndex": 0} if horizontal else {"type": "inside", "xAxisIndex": 0}
        ],
        "series": [
            {
                "name": "Receita",
                "type": "bar",
                "barMaxWidth": 28,
                "showBackground": True,
                "backgroundStyle": {"color": "rgba(148, 163, 184, 0.10)", "borderRadius": 5},
                "itemStyle": {
                    "borderRadius": [0, 4, 4, 0] if horizontal else [4, 4, 0, 0]
                },
                "emphasis": {"focus": "self", "itemStyle": {"shadowBlur": 12, "shadowColor": "rgba(15, 23, 42, 0.18)"}},
                "data": [
                    {
                        "value": round(float(value), 2),
                        "itemStyle": {"color": _CORES_GRAFICOS[i % len(_CORES_GRAFICOS)]},
                    }
                    for i, value in enumerate(valores)
                ],
            }
        ],
    }


# ---------------------------------------------------------------------------
# Filtros na sidebar recolhível
# ---------------------------------------------------------------------------
def barra_filtros(df: pd.DataFrame) -> dict:
    data_min = df["data_pedido"].min().date()
    data_max = df["data_pedido"].max().date()

    with st.sidebar:
        st.title("SIGE")
        st.caption("Sistema integrado de gestão")
        st.divider()
        st.subheader("Filtros")

        with st.expander("Período", expanded=True):
            periodo = st.date_input(
                "Período de análise",
                value=(data_min, data_max),
                min_value=data_min,
                max_value=data_max,
            )
            if not (isinstance(periodo, (tuple, list)) and len(periodo) == 2):
                periodo = (data_min, data_max)

        with st.expander("Região", expanded=True):
            regioes = st.multiselect(
                "Região",
                sorted(df["regiao"].dropna().unique().tolist()),
                placeholder="Todas as regiões",
            )
            paises_opcoes = df if not regioes else df[df["regiao"].isin(regioes)]
            paises = st.multiselect(
                "País",
                sorted(paises_opcoes["pais"].dropna().unique().tolist()),
                placeholder="Todos os países",
            )

        with st.expander("Veículos", expanded=False):
            modelos = st.multiselect(
                "Modelo",
                sorted(df["modelo"].dropna().unique().tolist()),
                placeholder="Todos os modelos",
            )
            anos_modelo = st.multiselect(
                "Ano do modelo",
                sorted(df["ano_modelo"].dropna().unique().tolist(), reverse=True),
                placeholder="Todos os anos",
            )

        with st.expander("Perfil do cliente", expanded=False):
            generos = st.multiselect(
                "Gênero",
                sorted(df["genero"].dropna().unique().tolist()),
                placeholder="Todos",
            )
            escolaridades = st.multiselect(
                "Escolaridade",
                sorted(df["escolaridade"].dropna().unique().tolist()),
                placeholder="Todas",
            )
            idade_min = int(df["idade"].min())
            idade_max = int(df["idade"].max())
            faixa_idade = st.slider(
                "Faixa etária",
                idade_min,
                idade_max,
                (idade_min, idade_max),
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
    st.caption("Visão geral de receita, performance regional e perfil dos clientes.")

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

    serie = D.serie_temporal(df, "W")
    with st.container(border=True):
        st.subheader("Tendência de receita e pedidos")
        st_echarts(
            _opcoes_linha(serie),
            height="390px",
            theme="streamlit",
            key="receita_periodo",
        )

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.subheader("Top 10 países")
            top = D.ranking(df, "pais", 10).sort_values("receita", ascending=False)
            st_echarts(
                _opcoes_barras(top["pais"], top["receita"], horizontal=True),
                height="360px",
                theme="streamlit",
                key="top_paises",
            )
    with c2:
        with st.container(border=True):
            st.subheader("Top 10 modelos")
            top = D.ranking(df, "modelo", 10).sort_values("receita", ascending=False)
            st_echarts(
                _opcoes_barras(top["modelo"], top["receita"], horizontal=True),
                height="360px",
                theme="streamlit",
                key="top_modelos",
            )

    c3, c4 = st.columns(2)
    with c3:
        with st.container(border=True):
            st.subheader("Receita por região")
            dist = D.distribuicao(df, "regiao")
            st_echarts(
                _opcoes_barras(dist["regiao"], dist["receita"], horizontal=False),
                height="320px",
                theme="streamlit",
                key="receita_regiao",
            )
    with c4:
        with st.container(border=True):
            st.subheader("Receita por faixa etária")
            fx = D.faixa_etaria(df)
            st_echarts(
                _opcoes_barras(fx["faixa"], fx["receita"], horizontal=False),
                height="320px",
                theme="streamlit",
                key="receita_faixa_etaria",
            )

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
        width="stretch",
        column_config={
            "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Receita": st.column_config.NumberColumn(format="$ %.0f"),
            "Nota": st.column_config.NumberColumn(format="%.2f"),
        },
    )


if __name__ == "__main__":
    main()
