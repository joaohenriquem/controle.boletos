# pages/1_Dashboard.py
# Dashboard principal — KPIs, gráficos e alertas

import streamlit as st
from services.auth_service import require_auth
from services.google_sheets_service import get_boletos, get_parametros
from services.dashboard_service import prepare_boletos_df, get_kpis, get_daily_totals
from services.previsao_service import (
    previsao_mensal, totais_por_categoria, totais_por_status, concentracao_por_dia_mes,
)
from components.cards import render_kpi_card, render_alert_card, render_limite_gauge
from components.charts import (
    chart_vencimentos_mes, chart_previsao_mensal,
    chart_por_categoria, chart_por_status, chart_concentracao_vencimentos,
)
from utils.formatters import format_currency
from utils.dates import today, month_name_br
from utils.constants import COLORS

st.set_page_config(page_title="Dashboard — Bem Estar Financeiro", page_icon="📊", layout="wide")

# Carregar CSS
try:
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

require_auth()

# Header
st.html("""
<div class="page-header">
    <h1>📊 Dashboard</h1>
    <p>Visão geral dos compromissos financeiros</p>
</div>
""")

# Carregar dados
with st.spinner("Carregando dados..."):
    df_raw = get_boletos()
    params = get_parametros()
    df = prepare_boletos_df(df_raw)
    limite = float(params.get("limite_maximo_diario", 1000))

# KPIs
kpis = get_kpis(df, limite)

col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi_card(
        "Vencendo Hoje",
        format_currency(kpis["valor_hoje"]),
        f"{kpis['qtd_hoje']} boleto(s)",
        "📅",
        COLORS["alerta"] if kpis["qtd_hoje"] > 0 else COLORS["primaria"],
    )
with col2:
    render_kpi_card(
        "Vencidos",
        format_currency(kpis["valor_vencidos"]),
        f"{kpis['qtd_vencidos']} boleto(s)",
        "🔴",
        COLORS["erro"] if kpis["qtd_vencidos"] > 0 else COLORS["primaria"],
    )
with col3:
    render_kpi_card(
        "Próximos 7 Dias",
        format_currency(kpis["valor_prox_7dias"]),
        "Previsão",
        "📆",
        COLORS["apoio"],
    )
with col4:
    render_kpi_card(
        "Total do Mês",
        format_currency(kpis["valor_mes"]),
        "Pendentes no mês",
        "🗓️",
        COLORS["primaria"],
    )

# Alerta de limite
st.markdown("<br>", unsafe_allow_html=True)
render_limite_gauge(kpis["percentual_limite"], kpis["valor_hoje"], limite)

if kpis["excedeu_limite"]:
    render_alert_card(
        f"O valor total de hoje ({format_currency(kpis['valor_hoje'])}) "
        f"excede o limite diário de {format_currency(limite)}!",
        "danger",
    )

if kpis["qtd_vencidos"] > 0:
    render_alert_card(
        f"Existem {kpis['qtd_vencidos']} boleto(s) vencido(s) "
        f"totalizando {format_currency(kpis['valor_vencidos'])}.",
        "warning",
    )

# Gráficos
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 📈 Análises")

t = today()
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    daily = get_daily_totals(df, t.year, t.month)
    fig = chart_vencimentos_mes(daily, limite, f"{month_name_br(t.month)} {t.year}")
    if fig:
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Sem dados de vencimentos para o mês atual.")

with col_chart2:
    df_prev = previsao_mensal(df)
    fig = chart_previsao_mensal(df_prev)
    if fig:
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Sem dados para previsão mensal.")

col_chart3, col_chart4 = st.columns(2)

with col_chart3:
    df_cat = totais_por_categoria(df)
    fig = chart_por_categoria(df_cat)
    if fig:
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Sem dados por categoria.")

with col_chart4:
    df_status = totais_por_status(df)
    fig = chart_por_status(df_status)
    if fig:
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Sem dados por status.")

# Concentração de vencimentos
df_conc = concentracao_por_dia_mes(df)
fig = chart_concentracao_vencimentos(df_conc)
if fig:
    st.plotly_chart(fig, width="stretch")
