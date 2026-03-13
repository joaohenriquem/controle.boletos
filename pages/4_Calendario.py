# pages/4_Calendario.py
# Calendário financeiro com visão mensal de vencimentos

import json
import calendar
import streamlit as st
import streamlit.components.v1 as components
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
    <p>Clique em um dia para ver os boletos</p>
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

year = st.session_state["cal_year"]
month = st.session_state["cal_month"]
daily_totals = get_daily_totals(df, year, month)


@st.dialog("📋 Boletos do Dia", width="large")
def _show_boletos_dialog(day: int):
    selected_date = date(year, month, day)
    boletos_dia = get_boletos_by_date(df, selected_date)
    total_dia = (
        boletos_dia["valor"].sum()
        if not boletos_dia.empty and "valor" in boletos_dia.columns
        else 0
    )
    st.markdown(f"### {format_date_br(selected_date)}")
    st.markdown(f"**{len(boletos_dia)} boleto(s)** — Total: **{format_currency(total_dia)}**")
    if boletos_dia.empty:
        st.info("Nenhum boleto para esta data.")
    else:
        st.markdown("---")
        render_boletos_table(boletos_dia)


# Build per-day style map
cal = calendar.monthcalendar(year, month)
weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
day_style: dict[int, dict] = {}

for week in cal:
    for day in week:
        if day == 0:
            continue
        total = daily_totals.get(day, 0)
        if total > limite:
            bg, border, day_color = "#FEE2E2", COLORS["erro"], "#7F1D1D"
        elif total > limite * 0.7:
            bg, border, day_color = "#FEF3C7", COLORS["alerta"], "#78350F"
        elif total > 0:
            bg, border, day_color = "#D1FAE5", COLORS["primaria"], "#064E3B"
        else:
            bg, border, day_color = "#FFFFFF", COLORS["borda"], "#1F2937"
        amount_str = f"R$ {total:,.0f}".replace(",", ".") if total > 0 else "—"
        day_style[day] = {
            "bg": bg, "border": border, "day_color": day_color, "amount": amount_str,
        }

# CSS: hover effect for all secondary buttons (calendar cells)
st.markdown("""<style>
button[data-testid="baseButton-secondary"] {
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}
button[data-testid="baseButton-secondary"]:hover {
    transform: scale(1.04) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}
</style>""", unsafe_allow_html=True)

# Weekday header row (HTML — purely visual)
header_cells = "".join(
    f'<div style="text-align:center;font-weight:700;font-size:0.85rem;color:#6B7280;'
    f'padding:0.5rem;background:#F7FAF8;border-radius:8px;">{w}</div>'
    for w in weekdays
)
st.html(
    f'<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:6px;margin-bottom:4px;">'
    f'{header_cells}</div>'
)

# Calendar button grid — one st.button per day
clicked_day = None
for week in cal:
    cols = st.columns(7)
    for col, day in zip(cols, week):
        if day == 0:
            with col:
                st.empty()
        else:
            info = day_style[day]
            is_today = (day == t.day and month == t.month and year == t.year)
            label = f"{day}{' ●' if is_today else ''}\n{info['amount']}"
            with col:
                if st.button(label, key=f"cal_{year}_{month}_{day}"):
                    clicked_day = day

# JS: apply per-day colors to the buttons using their text content
style_map_json = json.dumps({str(k): v for k, v in day_style.items()})
components.html(
    f"""<script>
(function() {{
  var SM = {style_map_json};
  function apply() {{
    window.parent.document
      .querySelectorAll('button[data-testid="baseButton-secondary"]')
      .forEach(function(b) {{
        var txt = (b.innerText || '').trim();
        var m = txt.match(/^(\\d+)/);
        if (!m) return;
        var s = SM[m[1]];
        if (!s) return;
        b.style.setProperty('background', s.bg, 'important');
        b.style.setProperty('border', '2px solid ' + s.border, 'important');
        b.style.setProperty('color', s.day_color, 'important');
        b.style.setProperty('min-height', '70px', 'important');
        b.style.setProperty('white-space', 'pre-line', 'important');
        b.style.setProperty('font-size', '0.82rem', 'important');
        b.style.setProperty('font-weight', '700', 'important');
        b.style.setProperty('border-radius', '10px', 'important');
        b.style.setProperty('padding', '0.4rem', 'important');
        b.style.setProperty('line-height', '1.4', 'important');
        b.style.setProperty('cursor', 'pointer', 'important');
        b.style.setProperty('width', '100%', 'important');
      }});
  }}
  setTimeout(apply, 50);
  setTimeout(apply, 250);
  setTimeout(apply, 700);
}})();
</script>""",
    height=0,
    scrolling=False,
)

if clicked_day is not None:
    _show_boletos_dialog(clicked_day)

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
    <span style="display:flex; align-items:center; gap:0.3rem;">
        <span style="width:14px; height:14px; background:#FFFFFF; border:2px solid {COLORS['borda']}; border-radius:3px;"></span>
        Sem boletos
    </span>
</div>
""")
