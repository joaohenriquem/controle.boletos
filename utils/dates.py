# utils/dates.py
# Funções auxiliares para manipulação de datas

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


def today() -> date:
    """Retorna a data de hoje."""
    return date.today()


def days_until(target: date) -> int:
    """Retorna quantos dias faltam até a data alvo."""
    return (target - today()).days


def is_overdue(vencimento: date, status: str) -> bool:
    """Verifica se um boleto está vencido (data passada e não pago)."""
    return vencimento < today() and status not in ("pago", "cancelado")


def date_range_this_month() -> tuple:
    """Retorna primeiro e último dia do mês atual."""
    t = today()
    first = t.replace(day=1)
    next_month = first + relativedelta(months=1)
    last = next_month - timedelta(days=1)
    return first, last


def date_range_next_month() -> tuple:
    """Retorna primeiro e último dia do próximo mês."""
    t = today()
    first = (t.replace(day=1) + relativedelta(months=1))
    last = (first + relativedelta(months=1)) - timedelta(days=1)
    return first, last


def next_n_days(n: int = 7) -> tuple:
    """Retorna hoje e a data daqui a n dias."""
    return today(), today() + timedelta(days=n)


def month_name_br(month: int) -> str:
    """Retorna nome do mês em português."""
    names = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março",
        4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro",
        10: "Outubro", 11: "Novembro", 12: "Dezembro",
    }
    return names.get(month, "")


def months_ahead(n: int = 6) -> list:
    """Retorna lista de (ano, mês) para os próximos n meses."""
    result = []
    t = today()
    for i in range(n):
        dt = t + relativedelta(months=i)
        result.append((dt.year, dt.month))
    return result


def parse_date_safe(value) -> date | None:
    """Tenta converter qualquer formato de data para objeto date."""
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
    return None
