# utils/formatters.py
# Funções de formatação para valores monetários, datas e textos

import locale
import unicodedata
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
    """Converte string monetária brasileira para float de forma ultra-robusta."""
    if isinstance(value_str, (int, float)):
        return float(value_str)
    if not value_str:
        return 0.0
    
    try:
        # Limpeza básica: remove R$, espaços e símbolos não numéricos
        cleaned = str(value_str).replace("R$", "").replace("\xa0", "").strip()
        cleaned = "".join(cleaned.split())
        
        if not cleaned:
            return 0.0
            
        # Tenta conversão direta (padrão float Python/US 1234.56)
        try:
            # Se for um número simples com apenas um ponto decimal opcional
            # No Brazil tendemos a usar vírgula, então se houver vírgula, pulamos para a lógica BR
            if "," not in cleaned:
                return float(cleaned)
        except:
            pass
            
        # Lógica de decisão de separador BR:
        if "." in cleaned and "," in cleaned:
            # Formato completo: 1.234,56 -> 1234.56
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            # Formato simples: 1234,56 -> 1234.56
            cleaned = cleaned.replace(",", ".")
        elif "." in cleaned:
            # Se houver apenas ponto (ex: 1.500 ou 1000.5)
            # No gspread/pandas, floats costumam vir como 1000.0 (ponto decimal)
            # No BR, costumam digitar 1.000 (ponto milhar)
            parts = cleaned.split(".")
            # Decisão: se a última parte tiver 1 ou 2 dígitos, tratamos como decimal (US/Standard)
            # Se tiver 3 dígitos, tratamos como milhar (1.000)
            if len(parts[-1]) in (1, 2):
                pass # Mantém o ponto
            else:
                cleaned = cleaned.replace(".", "")

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


def normalize_column_name(name: str) -> str:
    """Normaliza nome de coluna para permitir variações de cabeçalho."""
    if not isinstance(name, str):
        return ""
    # Remove acentos, espaços extras e caracteres especiais
    value = unicodedata.normalize("NFKD", name)
    value = "".join([c for c in value if not unicodedata.combining(c)])
    value = value.strip().lower()
    value = value.replace(" ", "_")
    value = value.replace("-", "_")
    return value
