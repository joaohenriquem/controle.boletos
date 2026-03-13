# pages/4_Calendario.py
# Calendário financeiro com visão mensal de vencimentos

import streamlit as st
import calendar
from datetime import date
from dateutil.relativedelta import relativedelta
from services.auth_service import require_auth
from services.google_sheets_service import get_boletos, get_parametros
from services.dashboard_service import prepare_boletos_df, get_daily_totals, get_boletos_by_date
from utils.formatters import format_currency, format_date_br, parse_currency
from utils.dates import today, month_name_br
from utils.constants import COLORS, DEFAULT_PARAMS
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
    
    # Busca o limite nos parâmetros, usando parse_currency para lidar com formatos BR
    raw_limite = params.get("limite_maximo_diario") or DEFAULT_PARAMS["limite_maximo_diario"]
    limite = parse_currency(raw_limite)
    
    # Se por algum motivo o parse falhar e retornar 0
    if limite <= 0:
        limite = 1500.0

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

# Renderizar calendário visual com wrapper de estilo base
st.markdown('<div class="cal-base-button-style">', unsafe_allow_html=True)

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
            
            # Determinar classe de marcador
            if total > limite:
                marker_cls = "marker-danger"
            elif total > limite * 0.7:
                marker_cls = "marker-warning"
            elif total > 0:
                marker_cls = "marker-ok"
            else:
                marker_cls = "marker-empty"
            
            today_cls = "marker-today" if is_today else ""
            
            # Formatar label do botão
            amount_str = f"R$ {total:,.0f}".replace(",", ".") if total > 0 else "—"
            label = f"{day}{' ●' if is_today else ''}\n\n{amount_str}"
            
            with col:
                # Injetamos o marcador que o CSS usará para pintar o botão seguinte
                st.html(f'<div class="calendar-marker {marker_cls} {today_cls}"></div>')
                if st.button(label, key=f"cal_{year}_{month}_{day}", use_container_width=True):
                    clicked_day = day

st.markdown('</div>', unsafe_allow_html=True) # Fim cal-base-button-style

if clicked_day:
    _show_boletos_dialog(clicked_day)

# Legenda
st.html(f"""
<div style="display:flex; gap:2rem; justify-content:center; margin:3rem 0; flex-wrap:wrap;">
    <span style="display:flex; align-items:center; gap:0.6rem; font-weight:800; font-size:1.2rem; color:#064E3B;">
        <span style="width:24px; height:24px; background:#D1FAE5; border:3px solid {COLORS['primaria']}; border-radius:8px;"></span>
        Dentro do limite
    </span>
    <span style="display:flex; align-items:center; gap:0.6rem; font-weight:800; font-size:1.2rem; color:#78350F;">
        <span style="width:24px; height:24px; background:#FEF3C7; border:3px solid {COLORS['alerta']}; border-radius:8px;"></span>
        Atenção (70-100%)
    </span>
    <span style="display:flex; align-items:center; gap:0.6rem; font-weight:800; font-size:1.2rem; color:#7F1D1D;">
        <span style="width:24px; height:24px; background:#FEE2E2; border:3px solid {COLORS['erro']}; border-radius:8px;"></span>
        Crítico (> Limite)
    </span>
</div>
""")
