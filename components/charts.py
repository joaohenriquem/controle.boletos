# components/charts.py
# Gráficos Plotly com identidade visual Bem Estar Financeiro

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.constants import COLORS, STATUS_COLORS
from utils.dates import month_name_br
from utils.formatters import format_currency


PLOTLY_LAYOUT = dict(
    font=dict(family="'Nunito', sans-serif", color=COLORS["texto"]),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=50, b=20),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.2,
        xanchor="center",
        x=0.5,
    ),
)


def chart_vencimentos_mes(daily_totals: dict, limite: float, month_name: str):
    """Gráfico de barras com vencimentos por dia no mês atual."""
    if not daily_totals:
        return None

    dias = sorted(daily_totals.keys())
    valores = [daily_totals[d] for d in dias]
    cores = [
        COLORS["erro"] if v > limite else
        COLORS["alerta"] if v > limite * 0.7 else
        COLORS["primaria"]
        for v in valores
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"Dia {d}" for d in dias],
        y=valores,
        marker_color=cores,
        text=[format_currency(v) for v in valores],
        textposition="auto",
        hovertemplate="Dia %{x}<br>Valor: %{text}<extra></extra>",
    ))

    # Linha de limite
    fig.add_hline(
        y=limite, line_dash="dash", line_color=COLORS["erro"],
        annotation_text=f"Limite: {format_currency(limite)}",
        annotation_position="top right",
    )

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=f"Vencimentos por Dia — {month_name}",
        xaxis_title="",
        yaxis_title="Valor (R$)",
        showlegend=False,
    )
    return fig


def chart_previsao_mensal(df_previsao: pd.DataFrame):
    """Gráfico de linha com previsão dos próximos meses."""
    if df_previsao.empty:
        return None

    df = df_previsao.copy()
    df["label"] = df.apply(
        lambda r: f"{month_name_br(int(r['mes']))[:3]}/{int(r['ano'])}",
        axis=1
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["label"],
        y=df["total"],
        mode="lines+markers+text",
        marker=dict(size=10, color=COLORS["primaria"]),
        line=dict(color=COLORS["primaria"], width=3),
        text=[format_currency(v) for v in df["total"]],
        textposition="top center",
        textfont=dict(size=10),
        hovertemplate="%{x}<br>Previsão: %{text}<extra></extra>",
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title="Previsão de Vencimentos — Próximos 6 Meses",
        xaxis_title="",
        yaxis_title="Valor (R$)",
    )
    return fig


def chart_por_categoria(df_categorias: pd.DataFrame):
    """Gráfico de rosca por categoria."""
    if df_categorias.empty:
        return None

    color_palette = [
        COLORS["primaria"], COLORS["apoio"], COLORS["secundaria"],
        COLORS["alerta"], "#8B5CF6", "#F97316", "#06B6D4",
        "#EC4899", "#84CC16", "#A78BFA",
    ]

    fig = go.Figure(data=[go.Pie(
        labels=df_categorias["categoria"],
        values=df_categorias["total"],
        hole=0.5,
        marker=dict(colors=color_palette[:len(df_categorias)]),
        textinfo="label+percent",
        textposition="outside",
        hovertemplate="%{label}<br>Valor: R$ %{value:,.2f}<br>%{percent}<extra></extra>",
    )])

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title="Distribuição por Categoria",
        showlegend=True,
    )
    return fig


def chart_por_status(df_status: pd.DataFrame):
    """Gráfico de barras por status."""
    if df_status.empty:
        return None

    cores = [STATUS_COLORS.get(s, "#9CA3AF") for s in df_status["status"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_status["status"],
        y=df_status["total"],
        marker_color=cores,
        text=[format_currency(v) for v in df_status["total"]],
        textposition="auto",
        hovertemplate="Status: %{x}<br>Valor: %{text}<br>Qtd: %{customdata}<extra></extra>",
        customdata=df_status["qtd"],
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title="Valores por Status",
        xaxis_title="",
        yaxis_title="Valor (R$)",
        showlegend=False,
    )
    return fig


def chart_concentracao_vencimentos(df_concentracao: pd.DataFrame):
    """Visual de concentração de vencimentos por dia do mês."""
    if df_concentracao.empty:
        return None

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_concentracao["dia_mes"],
        y=df_concentracao["total"],
        marker_color=COLORS["apoio"],
        text=[format_currency(v) for v in df_concentracao["total"]],
        textposition="auto",
        hovertemplate="Dia %{x}<br>Total: %{text}<br>Boletos: %{customdata}<extra></extra>",
        customdata=df_concentracao["qtd"],
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title="Concentração de Vencimentos por Dia do Mês",
        xaxis_title="Dia do Mês",
        yaxis_title="Valor Total (R$)",
        xaxis=dict(dtick=1),
        showlegend=False,
    )
    return fig
