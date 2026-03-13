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
    <p>Visualize seus compromissos no formato clássico, agora interativo</p>
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

@st.dialog("📋 Boletos do Dia", width="large")
def _show_boletos_dialog(day: int):
    selected_date = date(year, month, day)
    boletos_dia = get_boletos_by_date(df, selected_date)
    total_dia = boletos_dia["valor"].sum() if not boletos_dia.empty else 0
    st.markdown(f"### {format_date_br(selected_date)}")
    st.markdown(f"**{len(boletos_dia)} boleto(s)** — Total: **{format_currency(total_dia)}**")
    if boletos_dia.empty:
        st.info("Nenhum boleto para esta data.")
    else:
        st.markdown("---")
        render_boletos_table(boletos_dia)

# Renderizar calendário visual
cal = calendar.monthcalendar(year, month)
weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

# Header de dias da semana
cols_header = st.columns(7)
for col, wd in zip(cols_header, weekdays):
    col.markdown(f'<div class="calendar-header-cell">{wd}</div>', unsafe_allow_html=True)

# Grid de dias
clicked_day = None
for week in cal:
    cols = st.columns(7)
    for col, day in zip(cols, week):
        if day == 0:
            col.empty()
        else:
            total = daily_totals.get(day, 0)
            is_today = (day == t.day and month == t.month and year == t.year)
            
            # Determinar classe de cor
            if total > limite:
                cls = "cal-btn-danger"
            elif total > limite * 0.7:
                cls = "cal-btn-warning"
            elif total > 0:
                cls = "cal-btn-ok"
            else:
                cls = "cal-btn-empty"
            
            today_cls = "cal-btn-today" if is_today else ""
            
            # Formatar label do botão
            amount_str = f"R$ {total:,.0f}".replace(",", ".") if total > 0 else "—"
            # Label com o dia GRANDE e o valor em baixo
            label = f"{day}{' ●' if is_today else ''}\n\n{amount_str}"
            
            with col:
                st.markdown(f'<div class="cal-btn-wrapper {cls} {today_cls}">', unsafe_allow_html=True)
                if st.button(label, key=f"cal_{year}_{month}_{day}", use_container_width=True):
                    clicked_day = day
                st.markdown('</div>', unsafe_allow_html=True)

if clicked_day:
    _show_boletos_dialog(clicked_day)

# Legenda
st.html(f"""
<div style="display:flex; gap:1.5rem; justify-content:center; margin:2.5rem 0; flex-wrap:wrap;">
    <span style="display:flex; align-items:center; gap:0.5rem; font-weight:700; font-size:1.1rem;">
        <span style="width:20px; height:20px; background:#D1FAE5; border:3px solid {COLORS['primaria']}; border-radius:6px;"></span>
        Dentro do limite
    </span>
    <span style="display:flex; align-items:center; gap:0.5rem; font-weight:700; font-size:1.1rem;">
        <span style="width:20px; height:20px; background:#FEF3C7; border:3px solid {COLORS['alerta']}; border-radius:6px;"></span>
        Atenção (70-100%)
    </span>
    <span style="display:flex; align-items:center; gap:0.5rem; font-weight:700; font-size:1.1rem;">
        <span style="width:20px; height:20px; background:#FEE2E2; border:3px solid {COLORS['erro']}; border-radius:6px;"></span>
        Acima do limite
    </span>
</div>
""")
