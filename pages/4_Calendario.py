# pages/4_Calendario.py
# Calendário financeiro com visão mensal de vencimentos

import streamlit as st
import calendar
import json
from datetime import date
from dateutil.relativedelta import relativedelta
from services.auth_service import require_auth
from services.google_sheets_service import get_boletos, get_parametros
from services.dashboard_service import prepare_boletos_df, get_daily_totals, get_boletos_by_date
from utils.formatters import format_currency, format_date_br
from utils.dates import today, month_name_br
from utils.constants import COLORS
from components.tables import render_boletos_table
import streamlit.components.v1 as components

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

# Pre-calculate Styles
day_style: dict[int, dict] = {}
for week in cal:
    for day in week:
        if day == 0: continue
        total = daily_totals.get(day, 0)
        if total > limite:
            bg, border, color = "#FEE2E2", COLORS["erro"], "#7F1D1D"
        elif total > limite * 0.7:
            bg, border, color = "#FEF3C7", COLORS["alerta"], "#78350F"
        elif total > 0:
            bg, border, color = "#D1FAE5", COLORS["primaria"], "#064E3B"
        else:
            bg, border, color = "#FFFFFF", COLORS["borda"], "#1F2937"
        day_style[day] = {"bg": bg, "border": border, "color": color, "total": total}

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
            info = day_style[day]
            is_today = (day == t.day and month == t.month and year == t.year)
            
            # Formatar label do botão com o marcador invisível para o JS
            amount_str = f"R$ {info['total']:,.0f}".replace(",", ".") if info['total'] > 0 else "—"
            label = f"{day}{' ●' if is_today else ''}\n\n{amount_str}"
            
            with col:
                if st.button(label, key=f"cal_{year}_{month}_{day}", use_container_width=True):
                    clicked_day = day

if clicked_day:
    _show_boletos_dialog(clicked_day)

# JS Auto-Painter - Resiliente e Independente de wrappers
style_map_json = json.dumps({str(k): v for k, v in day_style.items()})
components.html(
    f"""<script>
(function() {{
  var SM = {style_map_json};
  var PRIMARIA = '{COLORS['primaria']}';

  function paint() {{
    var buttons = window.parent.document.querySelectorAll('button[data-testid="baseButton-secondary"]');
    buttons.forEach(function(b) {{
        var fullTxt = (b.innerText || '').trim();
        // Filtra partes vazias (causadas por \n\n)
        var parts = fullTxt.split('\\n').map(s => s.trim()).filter(Boolean);
        if (parts.length === 0) return;
        
        var firstPart = parts[0];
        var dayMatch = firstPart.match(/^(\\d+)/);
        if (!dayMatch) return;
        
        var dayNum = dayMatch[1];
        var s = SM[dayNum];
        if (!s) return;

        // Estilização base
        b.style.setProperty('background', s.bg, 'important');
        b.style.setProperty('border', '4px solid ' + s.border, 'important');
        b.style.setProperty('color', s.color, 'important');
        b.style.setProperty('min-height', '150px', 'important');
        b.style.setProperty('height', '100%', 'important');
        b.style.setProperty('border-radius', '24px', 'important');
        b.style.setProperty('white-space', 'pre-line', 'important');
        b.style.setProperty('transition', 'all 0.2s ease', 'important');
        b.style.setProperty('box-shadow', '0 6px 15px rgba(0,0,0,0.06)', 'important');
        b.style.setProperty('display', 'flex', 'important');
        b.style.setProperty('flex-direction', 'column', 'important');

        // Formatação do conteúdo se ainda não foi feito
        if (!b.getAttribute('data-v2-painted')) {{
            var dayLabel = parts[0]; 
            var valueLabel = parts.length > 1 ? parts[1] : '—';
            
            b.innerHTML = '<div style="display:flex; flex-direction:column; justify-content:space-between; height:100%; width:100%; pointer-events:none;">' + 
                          '<div style="font-size:2.2rem; font-weight:900; align-self:flex-start;">' + dayLabel + '</div>' + 
                          '<div style="font-size:1.1rem; font-weight:900; background:rgba(255,255,255,0.45); border-radius:12px; padding:8px 0; width:100%; text-align:center;">' + valueLabel + '</div>' +
                          '</div>';
            b.setAttribute('data-v2-painted', 'true');
        }}

        // Destaque "Hoje"
        if (fullTxt.includes('●')) {{
             b.style.setProperty('box-shadow', '0 0 0 5px ' + PRIMARIA + ', 0 15px 30px rgba(46, 139, 87, 0.4)', 'important');
        }}
    }});
  }}

  paint();
  setTimeout(paint, 500);
  setTimeout(paint, 1500);
  
  var obs = new MutationObserver(paint);
  obs.observe(window.parent.document.body, {{ childList: true, subtree: true }});
}})();
</script>""",
    height=0,
)

# Legenda
st.html(f"""
<div style="display:flex; gap:1.5rem; justify-content:center; margin:2rem 0; flex-wrap:wrap;">
    <span style="display:flex; align-items:center; gap:0.4rem; font-weight:600;">
        <span style="width:16px; height:16px; background:#D1FAE5; border:2px solid {COLORS['primaria']}; border-radius:4px;"></span>
        Dentro do limite
    </span>
    <span style="display:flex; align-items:center; gap:0.4rem; font-weight:600;">
        <span style="width:16px; height:16px; background:#FEF3C7; border:2px solid {COLORS['alerta']}; border-radius:4px;"></span>
        Atenção (70-100%)
    </span>
    <span style="display:flex; align-items:center; gap:0.4rem; font-weight:600;">
        <span style="width:16px; height:16px; background:#FEE2E2; border:2px solid {COLORS['erro']}; border-radius:4px;"></span>
        Acima do limite
    </span>
</div>
""")
