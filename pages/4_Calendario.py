# pages/4_Calendario.py
# Calendário financeiro com visão mensal de vencimentos

import streamlit as st
import calendar
from datetime import date
from dateutil.relativedelta import relativedelta
from services.auth_service import require_auth
from services.google_sheets_service import get_boletos, get_parametros
from services.dashboard_service import prepare_boletos_df, get_daily_totals, get_boletos_by_date
from utils.formatters import format_currency, format_date_br
from utils.dates import today, month_name_br
from utils.constants import COLORS
from components.tables import render_boletos_table

st.set_page_config(page_title="Calendário — Bem Estar Financeiro", page_icon="📅", layout="wide")

try:
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

require_auth()

st.html("""
<div class="page-header">
    <h1>📅 Calendário Financeiro</h1>
    <p>Visualize seus compromissos em formato de calendário</p>
</div>
""")

# Carregar dados
with st.spinner("Carregando dados..."):
    df_raw = get_boletos()
    params = get_parametros()
    df = prepare_boletos_df(df_raw)
    limite = float(params.get("limite_maximo_diario", 15000))

# Navegação de mês
t = today()
if "cal_year" not in st.session_state:
    st.session_state["cal_year"] = t.year
if "cal_month" not in st.session_state:
    st.session_state["cal_month"] = t.month

col_nav1, col_nav2, col_nav3 = st.columns([1, 3, 1])

with col_nav1:
    if st.button("◀ Mês anterior"):
        dt = date(st.session_state["cal_year"], st.session_state["cal_month"], 1) - relativedelta(months=1)
        st.session_state["cal_year"] = dt.year
        st.session_state["cal_month"] = dt.month
        st.rerun()

with col_nav2:
    st.markdown(
        f"<h2 style='text-align:center; color:{COLORS['primaria']};'>"
        f"{month_name_br(st.session_state['cal_month'])} {st.session_state['cal_year']}"
        f"</h2>",
        unsafe_allow_html=True,
    )

with col_nav3:
    if st.button("Mês seguinte ▶"):
        dt = date(st.session_state["cal_year"], st.session_state["cal_month"], 1) + relativedelta(months=1)
        st.session_state["cal_year"] = dt.year
        st.session_state["cal_month"] = dt.month
        st.rerun()

# Obter totais diários
year = st.session_state["cal_year"]
month = st.session_state["cal_month"]
daily_totals = get_daily_totals(df, year, month)

# Renderizar calendário visual em HTML
cal = calendar.monthcalendar(year, month)
weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

html = '<div class="calendar-grid">'
# Header
for wd in weekdays:
    html += f'<div class="calendar-header-cell">{wd}</div>'

# Dias
for week in cal:
    for day in week:
        if day == 0:
            html += '<div class="calendar-cell empty"></div>'
        else:
            total = daily_totals.get(day, 0)
            is_today = (day == t.day and month == t.month and year == t.year)

            # Cor baseada no limite
            if total > limite:
                bg = "#FEE2E2"
                border = COLORS["erro"]
                value_color = "#991B1B"
                day_color = "#7F1D1D"
            elif total > limite * 0.7:
                bg = "#FEF3C7"
                border = COLORS["alerta"]
                value_color = "#92400E"
                day_color = "#78350F"
            elif total > 0:
                bg = "#D1FAE5"
                border = COLORS["primaria"]
                value_color = "#065F46"
                day_color = "#064E3B"
            else:
                bg = "#FFFFFF"
                border = COLORS["borda"]
                value_color = "#6B7280"
                day_color = "#1F2937"

            today_class = "today" if is_today else ""

            html += f'''
            <div class="calendar-cell {today_class}" style="background:{bg}; border:2px solid {border};">
                <div class="calendar-day" style="color:{day_color};">{day}</div>
                <div class="calendar-value" style="color:{value_color};">
                    {"R$ " + f"{total:,.0f}".replace(",", ".") if total > 0 else "—"}
                </div>
            </div>
            '''

html += '</div>'

st.html(html)

# Legenda
st.html(f"""
<div style="display:flex; gap:1.5rem; justify-content:center; margin:1rem 0; flex-wrap:wrap;">
    <span style="display:flex; align-items:center; gap:0.3rem;">
        <span style="width:14px; height:14px; background:#D1FAE5; border:2px solid {COLORS['primaria']}; border-radius:3px;"></span>
        Dentro do limite
    </span>
    <span style="display:flex; align-items:center; gap:0.3rem;">
        <span style="width:14px; height:14px; background:#FEF3C7; border:2px solid {COLORS['alerta']}; border-radius:3px;"></span>
        Atenção (70-100%)
    </span>
    <span style="display:flex; align-items:center; gap:0.3rem;">
        <span style="width:14px; height:14px; background:#FEE2E2; border:2px solid {COLORS['erro']}; border-radius:3px;"></span>
        Acima do limite
    </span>
</div>
""")

# Seleção de dia
st.markdown("---")
st.markdown("### 📋 Boletos do Dia Selecionado")

max_day = calendar.monthrange(year, month)[1]
selected_day = st.slider("Selecione o dia", min_value=1, max_value=max_day, value=min(t.day, max_day))

selected_date = date(year, month, selected_day)
boletos_dia = get_boletos_by_date(df, selected_date)

st.markdown(f"**{format_date_br(selected_date)}** — {len(boletos_dia)} boleto(s)")

if not boletos_dia.empty:
    render_boletos_table(boletos_dia)
else:
    st.info("Nenhum boleto para esta data.")
