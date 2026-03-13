# components/cards.py
# Componentes de cards KPI para o dashboard

import streamlit as st
from utils.formatters import format_currency
from utils.constants import COLORS


def render_kpi_card(title: str, value: str, subtitle: str = "", icon: str = "", color: str = ""):
    """Renderiza um card KPI estilizado."""
    border_color = color or COLORS["primaria"]
    st.html(f"""
    <div class="kpi-card" style="border-left: 4px solid {border_color};">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-subtitle">{subtitle}</div>
    </div>
    """)


def render_alert_card(message: str, alert_type: str = "warning"):
    """Renderiza um card de alerta."""
    colors = {
        "warning": {"bg": "#FEF3C7", "border": COLORS["alerta"], "icon": "⚠️"},
        "danger": {"bg": "#FEE2E2", "border": COLORS["erro"], "icon": "🚨"},
        "success": {"bg": "#D1FAE5", "border": COLORS["primaria"], "icon": "✅"},
        "info": {"bg": "#DBEAFE", "border": COLORS["apoio"], "icon": "ℹ️"},
    }
    style = colors.get(alert_type, colors["info"])

    st.html(f"""
    <div class="alert-card" style="
        background: {style['bg']};
        border-left: 4px solid {style['border']};
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    ">
        <span style="font-size: 1.4rem;">{style['icon']}</span>
        <span style="color: {COLORS['texto']}; font-size: 0.95rem;">{message}</span>
    </div>
    """)


def render_status_badge(status: str) -> str:
    """Retorna HTML de um badge de status."""
    colors = {
        "pendente": {"bg": "#FEF3C7", "text": "#92400E"},
        "pago": {"bg": "#D1FAE5", "text": "#065F46"},
        "vencido": {"bg": "#FEE2E2", "text": "#991B1B"},
        "cancelado": {"bg": "#F3F4F6", "text": "#6B7280"},
    }
    style = colors.get(status, {"bg": "#F3F4F6", "text": "#6B7280"})
    return (
        f'<span style="background:{style["bg"]}; color:{style["text"]}; '
        f'padding:3px 10px; border-radius:12px; font-size:0.8rem; '
        f'font-weight:600; text-transform:uppercase;">{status}</span>'
    )


def render_limite_gauge(percentual: float, valor_hoje: float, limite: float):
    """Renderiza indicador visual do limite diário."""
    if percentual <= 70:
        color = COLORS["primaria"]
        label = "Normal"
    elif percentual <= 100:
        color = COLORS["alerta"]
        label = "Atenção"
    else:
        color = COLORS["erro"]
        label = "Excedido"

    bar_width = min(percentual, 100)

    st.html(f"""
    <div class="limite-gauge">
        <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
            <span style="font-weight:600; color:{COLORS['texto']};">Limite Diário</span>
            <span style="font-weight:700; color:{color};">{label} — {percentual:.0f}%</span>
        </div>
        <div style="background:#E5E7EB; border-radius:8px; height:12px; overflow:hidden;">
            <div style="background:{color}; width:{bar_width}%; height:100%; border-radius:8px;
                        transition: width 0.5s ease;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:0.35rem;
                    font-size:0.8rem; color:{COLORS['texto_secundario']};">
            <span>{format_currency(valor_hoje)} hoje</span>
            <span>Limite: {format_currency(limite)}</span>
        </div>
    </div>
    """)
