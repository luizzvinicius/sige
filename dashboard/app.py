"""Dashboard SIGE — gráficos em Apache ECharts (streamlit-echarts)."""
from __future__ import annotations

import sys
from pathlib import Path

import data as D
import pandas as pd
import streamlit as st
from streamlit_echarts import JsCode, st_echarts

sys.path.insert(0, str(Path(__file__).resolve().parent))

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
        [data-testid="stSidebar"] :is([data-testid="stDownloadButton"], [data-testid="stButton"]) button,
        [data-testid="stSidebar"] :is([data-testid="stDownloadButton"], [data-testid="stButton"]) button * {
            color: #172438 !important;
            -webkit-text-fill-color: #172438 !important;
        }
        [data-testid="stSidebar"] :is([data-testid="stDownloadButton"], [data-testid="stButton"]) button:hover,
        [data-testid="stSidebar"] :is([data-testid="stDownloadButton"], [data-testid="stButton"]) button:focus,
        [data-testid="stSidebar"] :is([data-testid="stDownloadButton"], [data-testid="stButton"]) button:active {
            background: #E9EFF7 !important;
            border-color: #C7D3E3 !important;
        }
        [data-testid="stSidebar"] :is([data-testid="stDownloadButton"], [data-testid="stButton"]) button:disabled,
        [data-testid="stSidebar"] :is([data-testid="stDownloadButton"], [data-testid="stButton"]) button:disabled * {
            color: #9AA8BC !important;
            -webkit-text-fill-color: #9AA8BC !important;
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


def _csv_filtrado(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")


def _tem_filtro_ativo(df_total: pd.DataFrame, filtros: dict) -> bool:
    """Indica se ao menos um filtro saiu do valor padrão (faixa completa)."""
    periodo = filtros.get("periodo")
    data_min = df_total["data_pedido"].min().date()
    data_max = df_total["data_pedido"].max().date()
    if tuple(periodo) != (data_min, data_max):
        return True
    if any(
        filtros.get(chave)
        for chave in (
            "regioes",
            "paises",
            "modelos",
            "anos_modelo",
            "generos",
            "escolaridades",
        )
    ):
        return True
    faixa = filtros.get("faixa_idade")
    return bool(faixa) and tuple(faixa) != (
        int(df_total["idade"].min()),
        int(df_total["idade"].max()),
    )


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
        "legend": {"bottom": 4, "icon": "none"},
        "toolbox": {
            "right": 8,
            "feature": {
                "dataZoom": {"yAxisIndex": "none"} if horizontal else {"xAxisIndex": "none"},
                "magicType": {"type": ["line", "bar"]},
                "restore": {},
                "saveAsImage": {"pixelRatio": 2},
            },
        },
        "grid": {"left": 12, "right": 28, "top": 42, "bottom": 42, "containLabel": True},
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


def _opcoes_unidades_por_modelo(df: pd.DataFrame) -> dict:
    """Cria barras coloridas com unidades vendidas no conjunto já filtrado."""
    vendas = (
        df.groupby("modelo", as_index=False)["quantidade"]
        .sum()
        .sort_values("quantidade", ascending=False)
    )
    cores = ["#3B82F6", "#8B5CF6", "#F97316", "#22C55E"]

    return {
        "color": cores,
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "valueFormatter": JsCode(
                "function (value) {"
                " return Number(value).toLocaleString('pt-BR') + ' unidades';"
                "}"
            ),
        },
        "legend": {"bottom": 4, "icon": "none"},
        "toolbox": {
            "right": 8,
            "feature": {
                "dataZoom": {"yAxisIndex": "none"},
                "restore": {},
                "saveAsImage": {"pixelRatio": 2},
            },
        },
        "grid": {"left": 16, "right": 24, "top": 36, "bottom": 42, "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": vendas["modelo"].astype(str).tolist(),
            "axisTick": {"show": False},
        },
        "yAxis": {
            "type": "value",
            "min": 0,
            "axisLabel": {
                "formatter": JsCode(
                    "function (value) {"
                    " return Number(value).toLocaleString('pt-BR');"
                    "}"
                )
            },
            "splitLine": {"lineStyle": {"type": "dashed", "color": "#DCE4EF"}},
        },
        "dataZoom": [{"type": "inside", "xAxisIndex": 0}],
        "series": [
            {
                "name": "Unidades vendidas",
                "type": "bar",
                "barMaxWidth": 64,
                "showBackground": True,
                "backgroundStyle": {
                    "color": "rgba(148, 163, 184, 0.10)",
                    "borderRadius": [6, 6, 0, 0],
                },
                "itemStyle": {"borderRadius": [6, 6, 0, 0]},
                "emphasis": {
                    "focus": "self",
                    "itemStyle": {
                        "shadowBlur": 12,
                        "shadowColor": "rgba(15, 23, 42, 0.18)",
                    },
                },
                "data": [
                    {
                        "value": int(row.quantidade),
                        "itemStyle": {"color": cores[i % len(cores)]},
                    }
                    for i, row in enumerate(vendas.itertuples(index=False))
                ],
            }
        ],
    }


def _opcoes_participacao_modelos(df: pd.DataFrame) -> dict:
    """Cria uma rosca com a participação de cada modelo no faturamento filtrado."""
    participacao = (
        df.groupby("modelo")["faturamento"]
        .sum()
        .sort_values(ascending=False)
    )
    cores = _CORES_GRAFICOS
    dados = [
        {
            "name": str(modelo),
            "value": round(float(valor), 2),
            "itemStyle": {"color": cores[i % len(cores)]},
        }
        for i, (modelo, valor) in enumerate(participacao.items())
    ]

    return {
        "color": cores,
        "tooltip": {
            "trigger": "item",
            "formatter": JsCode(
                "function (item) {"
                " return item.marker + ' ' + item.name + '<br/>'"
                "  + 'Faturamento: US$ '"
                "  + Number(item.value).toLocaleString('pt-BR',"
                "    {minimumFractionDigits: 2, maximumFractionDigits: 2})"
                "  + '<br/>Participação: ' + item.percent.toFixed(1) + '%';"
                "}"
            ),
        },
        "legend": {"type": "scroll", "bottom": 4, "left": "center"},
        "toolbox": {
            "right": 8,
            "feature": {
                "restore": {},
                "saveAsImage": {"pixelRatio": 2},
            },
        },
        "series": [
            {
                "name": "Participação no faturamento",
                "type": "pie",
                "radius": ["44%", "72%"],
                "center": ["50%", "46%"],
                "selectedMode": "single",
                "avoidLabelOverlap": True,
                "itemStyle": {
                    "borderColor": "#FFFFFF",
                    "borderWidth": 3,
                },
                "label": {"show": False},
                "labelLine": {"show": False},
                "emphasis": {
                    "scale": True,
                    "scaleSize": 8,
                    "label": {
                        "show": True,
                        "fontSize": 16,
                        "fontWeight": "bold",
                        "formatter": JsCode(
                            "function (item) {"
                            " return item.name + '\\n' + item.percent.toFixed(1) + '%';"
                            "}"
                        ),
                    },
                },
                "data": dados,
            }
        ],
    }


def _opcoes_media_por_modelo(
    df: pd.DataFrame,
    coluna: str,
    indicador: str,
    *,
    moeda: bool = False,
    escala_maxima: float | None = None,
) -> dict:
    """Monta barras com a média filtrada de um indicador por modelo."""
    medias = df.groupby("modelo")[coluna].mean().dropna().sort_index()
    cores = _CORES_GRAFICOS
    formatador = (
        _formatter_moeda()
        if moeda
        else JsCode(
            "function (value) {"
            " return Number(value).toLocaleString('pt-BR',"
            "  {maximumFractionDigits: 2});"
            "}"
        )
    )
    y_axis = {
        "type": "value",
        "min": 0,
        "axisLabel": {"formatter": formatador},
        "splitLine": {"lineStyle": {"type": "dashed", "color": "#DCE4EF"}},
    }
    if escala_maxima is not None:
        y_axis["max"] = escala_maxima

    return {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "valueFormatter": formatador,
        },
        "legend": {"bottom": 4, "icon": "none"},
        "toolbox": {
            "right": 8,
            "feature": {
                "restore": {},
                "saveAsImage": {"pixelRatio": 2},
            },
        },
        "grid": {"left": 20, "right": 24, "top": 30, "bottom": 50, "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": medias.index.astype(str).tolist(),
            "axisTick": {"show": False},
        },
        "yAxis": y_axis,
        "series": [
            {
                "name": indicador,
                "type": "bar",
                "barMaxWidth": 80,
                "emphasis": {
                    "focus": "self",
                    "itemStyle": {
                        "shadowBlur": 12,
                        "shadowColor": "rgba(15, 23, 42, 0.18)",
                    },
                },
                "data": [
                    {
                        "value": round(float(valor), 2),
                        "itemStyle": {
                            "color": cores[i % len(cores)],
                            "borderRadius": [8, 8, 0, 0],
                        },
                    }
                    for i, valor in enumerate(medias)
                ],
            }
        ],
    }


def _opcoes_escolaridade(df: pd.DataFrame) -> dict:
    """Mostra a participação de compradores distintos por escolaridade."""
    compradores = (
        df.dropna(subset=["escolaridade"])
        .groupby("escolaridade")["id_cliente"]
        .nunique()
        .sort_values(ascending=False)
    )
    cores = _CORES_GRAFICOS

    return {
        "color": cores,
        "tooltip": {
            "trigger": "item",
            "formatter": JsCode(
                "function (item) {"
                " return item.marker + ' ' + item.name + '<br/>'"
                "  + Number(item.value).toLocaleString('pt-BR')"
                "  + ' compradores (' + item.percent.toFixed(1) + '%)';"
                "}"
            ),
        },
        "legend": {"type": "scroll", "bottom": 4, "left": "center"},
        "toolbox": {
            "right": 8,
            "feature": {
                "restore": {},
                "saveAsImage": {"pixelRatio": 2},
            },
        },
        "series": [
            {
                "name": "Compradores por escolaridade",
                "type": "pie",
                "radius": ["44%", "72%"],
                "center": ["50%", "46%"],
                "selectedMode": "single",
                "avoidLabelOverlap": True,
                "itemStyle": {"borderColor": "#FFFFFF", "borderWidth": 3},
                "label": {"show": False},
                "labelLine": {"show": False},
                "emphasis": {
                    "scale": True,
                    "scaleSize": 8,
                    "label": {
                        "show": True,
                        "fontSize": 15,
                        "fontWeight": "bold",
                        "formatter": JsCode(
                            "function (item) {"
                            " return item.name + '\\n' + item.percent.toFixed(1) + '%';"
                            "}"
                        ),
                    },
                },
                "data": [
                    {
                        "name": str(escolaridade),
                        "value": int(total),
                        "itemStyle": {"color": cores[i % len(cores)]},
                    }
                    for i, (escolaridade, total) in enumerate(compradores.items())
                ],
            }
        ],
    }


_METRICAS_GEOGRAFICAS = {
    "Faturamento": ("faturamento", "moeda"),
    "Receita líquida": ("receita_liquida", "moeda"),
    "Unidades vendidas": ("quantidade", "quantidade"),
    "Pedidos": ("id_pedido", "quantidade"),
}


def _agregar_desempenho_geografico(
    df: pd.DataFrame,
    dimensao: str,
    indicador: str,
) -> pd.DataFrame:
    coluna, _ = _METRICAS_GEOGRAFICAS[indicador]
    agrupamento = df.groupby(dimensao)
    if coluna == "id_pedido":
        serie = agrupamento[coluna].nunique()
    else:
        serie = agrupamento[coluna].sum()
    return (
        serie.rename("valor")
        .sort_values(ascending=False)
        .reset_index()
    )


def _opcoes_desempenho_geografico(
    dados: pd.DataFrame,
    dimensao: str,
    indicador: str,
) -> dict:
    """Monta o gráfico geográfico para a dimensão e métrica selecionadas."""
    _, formato = _METRICAS_GEOGRAFICAS[indicador]
    moeda = formato == "moeda"
    formatador = (
        _formatter_moeda()
        if moeda
        else JsCode(
            "function (value) {"
            " return Number(value).toLocaleString('pt-BR');"
            "}"
        )
    )
    rotacionar = len(dados) > 5
    zoom = [{"type": "inside", "xAxisIndex": 0}]
    if len(dados) > 8:
        zoom.append(
            {"type": "slider", "xAxisIndex": 0, "height": 12, "bottom": 28}
        )
    rotulo_eixo = {
        "rotate": 30 if rotacionar else 0,
        "hideOverlap": True,
    }
    if rotacionar:
        rotulo_eixo["formatter"] = JsCode(
            "function (value) {"
            " value = String(value);"
            " return value.length > 16 ? value.slice(0, 14) + '...' : value;"
            "}"
        )

    return {
        "color": _CORES_GRAFICOS,
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "valueFormatter": formatador,
        },
        "legend": {"top": 8, "left": 12, "icon": "none"},
        "toolbox": {
            "right": 8,
            "feature": {
                "dataZoom": {"yAxisIndex": "none"},
                "restore": {},
                "saveAsImage": {"pixelRatio": 2},
            },
        },
        "grid": {
            "left": 16,
            "right": 24,
            "top": 38,
            "bottom": 100 if rotacionar else 48,
            "containLabel": True,
        },
        "xAxis": {
            "type": "category",
            "data": dados[dimensao].astype(str).tolist(),
            "axisTick": {"show": False},
            "axisLabel": rotulo_eixo,
        },
        "yAxis": {
            "type": "value",
            "min": 0,
            "axisLabel": {"formatter": formatador},
            "splitLine": {"lineStyle": {"type": "dashed", "color": "#DCE4EF"}},
        },
        "dataZoom": zoom,
        "series": [
            {
                "name": indicador,
                "type": "bar",
                "barMaxWidth": 72,
                "showBackground": True,
                "backgroundStyle": {
                    "color": "rgba(148, 163, 184, 0.10)",
                    "borderRadius": [6, 6, 0, 0],
                },
                "itemStyle": {"borderRadius": [6, 6, 0, 0]},
                "emphasis": {
                    "focus": "self",
                    "itemStyle": {
                        "shadowBlur": 12,
                        "shadowColor": "rgba(15, 23, 42, 0.18)",
                    },
                },
                "data": [
                    {
                        "value": (
                            round(float(valor), 2)
                            if moeda
                            else int(valor)
                        ),
                        "itemStyle": {
                            "color": _CORES_GRAFICOS[i % len(_CORES_GRAFICOS)]
                        },
                    }
                    for i, valor in enumerate(dados["valor"])
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

    filtro_ativo = _tem_filtro_ativo(df_total, filtros)

    with st.sidebar:
        st.divider()
        if filtro_ativo:
            st.session_state["aviso_exportar_sem_filtro"] = False
            st.download_button(
                "Exportar dados atuais",
                data=_csv_filtrado(df),
                file_name="sige_dados_filtrados.csv",
                mime="text/csv",
                use_container_width=True,
                key="exportar_dados_atuais",
            )
            st.caption(f"{len(df):,} registros nos filtros atuais".replace(",", "."))
        else:
            if st.button(
                "Exportar dados atuais",
                use_container_width=True,
                key="exportar_dados_atuais_sem_filtro",
            ):
                st.session_state["aviso_exportar_sem_filtro"] = True
            if st.session_state.get("aviso_exportar_sem_filtro"):
                st.error("Selecione ao menos um filtro para exportar os dados.")

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

    with st.container(border=True):
        st.subheader("Desempenho geográfico")
        col_dimensao, col_indicador = st.columns(2)
        with col_dimensao:
            agrupamento = st.selectbox(
                "Agrupar",
                ["Por região", "Por país"],
                key="desempenho_geografico_dimensao",
            )
        with col_indicador:
            indicador = st.selectbox(
                "Indicador",
                list(_METRICAS_GEOGRAFICAS),
                key="desempenho_geografico_indicador",
            )

        dimensao = "regiao" if agrupamento == "Por região" else "pais"
        dados_geograficos = _agregar_desempenho_geografico(
            df,
            dimensao,
            indicador,
        )
        st_echarts(
            _opcoes_desempenho_geografico(
                dados_geograficos,
                dimensao,
                indicador,
            ),
            height="390px",
            theme="streamlit",
            key="desempenho_geografico",
        )

    coluna_esquerda, coluna_direita = st.columns(2)
    with coluna_esquerda:
        with st.container(border=True):
            st.subheader("Unidades vendidas por modelo")
            st_echarts(
                _opcoes_unidades_por_modelo(df),
                height="330px",
                theme="streamlit",
                key="unidades_por_modelo",
            )
    with coluna_direita:
        with st.container(border=True):
            st.subheader("Participação dos modelos no faturamento")
            st_echarts(
                _opcoes_participacao_modelos(df),
                height="350px",
                theme="streamlit",
                key="participacao_modelos_faturamento",
            )

    coluna_esquerda, coluna_direita = st.columns(2)
    with coluna_esquerda:
        with st.container(border=True):
            st.subheader("Receita por faixa etária")
            fx = D.faixa_etaria(df)
            st_echarts(
                _opcoes_barras(fx["faixa"], fx["receita"], horizontal=False),
                height="320px",
                theme="streamlit",
                key="receita_faixa_etaria",
            )
    with coluna_direita:
        with st.container(border=True):
            st.subheader("Desconto médio por modelo")
            st_echarts(
                _opcoes_media_por_modelo(
                    df,
                    "desconto",
                    "Desconto médio",
                    moeda=True,
                ),
                height="320px",
                theme="streamlit",
                key="desconto_medio_modelo",
            )

    coluna_esquerda, coluna_direita = st.columns(2)
    with coluna_esquerda:
        with st.container(border=True):
            st.subheader("Avaliação dos clientes por modelo")
            st_echarts(
                _opcoes_media_por_modelo(
                    df,
                    "avaliacao_cliente",
                    "Avaliação média",
                    escala_maxima=5,
                ),
                height="320px",
                theme="streamlit",
                key="avaliacao_clientes_modelo",
            )
    with coluna_direita:
        with st.container(border=True):
            st.subheader("Perfil dos compradores por escolaridade")
            st_echarts(
                _opcoes_escolaridade(df),
                height="350px",
                theme="streamlit",
                key="perfil_escolaridade",
            )

if __name__ == "__main__":
    main()
