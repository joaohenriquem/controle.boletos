# utils/formatters.py
# Funções de formatação para valores monetários, datas e textos

import locale
from datetime import datetime, date


def format_currency(value: float) -> str:
    """Formata valor como moeda brasileira (R$ 1.234,56)."""
    try:
        val = float(value)
        formatted = f"{val:,.2f}"
        # Converter formato americano para brasileiro
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"
    except (ValueError, TypeError):
        return "R$ 0,00"


def format_date_br(dt) -> str:
    """Formata data no padrão brasileiro (dd/mm/aaaa)."""
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, "%Y-%m-%d").date()
        except ValueError:
            try:
                dt = datetime.strptime(dt, "%d/%m/%Y").date()
            except ValueError:
                return dt
    if isinstance(dt, (datetime, date)):
        return dt.strftime("%d/%m/%Y")
    return str(dt)


def parse_date(date_str: str) -> date:
    """Tenta converter string em objeto date, suportando múltiplos formatos."""
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    raise ValueError(f"Formato de data não reconhecido: {date_str}")


def parse_currency(value_str) -> float:
    """Converte string monetária brasileira para float."""
    if isinstance(value_str, (int, float)):
        return float(value_str)
    if not value_str:
        return 0.0
    try:
        # Remove R$, espaços normais e espaços inquebráveis
        cleaned = str(value_str).replace("R$", "").replace("\xa0", "").strip()
        cleaned = "".join(cleaned.split()) # Remove qualquer outro whitespace
        
        if not cleaned:
            return 0.0
            
        # Formato brasileiro: 1.234,56 -> 1234.56
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0


def truncate_text(text: str, max_length: int = 50) -> str:
    """Trunca texto com reticências se exceder o limite."""
    if not text:
        return ""
    return text[:max_length] + "..." if len(text) > max_length else text


def status_emoji(status: str) -> str:
    """Retorna emoji correspondente ao status."""
    mapping = {
        "pendente": "🟡",
        "pago": "🟢",
        "vencido": "🔴",
        "cancelado": "⚫",
    }
    return mapping.get(status, "⚪")
