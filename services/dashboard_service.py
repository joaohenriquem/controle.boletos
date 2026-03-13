# services/dashboard_service.py
# Lógica de negócio para o dashboard e KPIs

import pandas as pd
from datetime import date, timedelta
from utils.dates import today, date_range_this_month, next_n_days, parse_date_safe
from utils.formatters import parse_currency
from utils.constants import STATUS_PAGO, STATUS_CANCELADO


def prepare_boletos_df(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara DataFrame de boletos com tipos corretos."""
    if df.empty:
        return df

    df = df.copy()
    df["data_vencimento"] = df["data_vencimento"].apply(parse_date_safe)
    df["data_emissao"] = df["data_emissao"].apply(parse_date_safe)
    df["valor"] = df["valor"].apply(parse_currency)

    # Atualizar status de vencidos automaticamente
    t = today()
    mask = (
        df["data_vencimento"].notna() &
        (df["data_vencimento"] < t) &
        (~df["status"].isin([STATUS_PAGO, STATUS_CANCELADO]))
    )
    df.loc[mask, "status"] = "vencido"

    return df


def get_kpis(df: pd.DataFrame, limite_diario: float) -> dict:
    """Calcula os KPIs do dashboard."""
    t = today()
    first_month, last_month = date_range_this_month()
    _, next_7 = next_n_days(7)

    # Filtros
    hoje_mask = df["data_vencimento"] == t
    vencidos_mask = (df["data_vencimento"] < t) & (~df["status"].isin([STATUS_PAGO, STATUS_CANCELADO]))
    prox7_mask = (df["data_vencimento"] >= t) & (df["data_vencimento"] <= next_7) & (~df["status"].isin([STATUS_PAGO, STATUS_CANCELADO]))
    mes_mask = (df["data_vencimento"] >= first_month) & (df["data_vencimento"] <= last_month) & (~df["status"].isin([STATUS_PAGO, STATUS_CANCELADO]))
    hoje_pendente = hoje_mask & (~df["status"].isin([STATUS_PAGO, STATUS_CANCELADO]))

    total_hoje = df.loc[hoje_pendente, "valor"].sum() if not df.empty else 0
    percentual_limite = (total_hoje / limite_diario * 100) if limite_diario > 0 else 0

    return {
        "qtd_hoje": int(hoje_pendente.sum()) if not df.empty else 0,
        "valor_hoje": total_hoje,
        "qtd_vencidos": int(vencidos_mask.sum()) if not df.empty else 0,
        "valor_vencidos": df.loc[vencidos_mask, "valor"].sum() if not df.empty else 0,
        "valor_prox_7dias": df.loc[prox7_mask, "valor"].sum() if not df.empty else 0,
        "valor_mes": df.loc[mes_mask, "valor"].sum() if not df.empty else 0,
        "limite_diario": limite_diario,
        "percentual_limite": percentual_limite,
        "excedeu_limite": total_hoje > limite_diario,
    }


def get_daily_totals(df: pd.DataFrame, year: int, month: int) -> dict:
    """Retorna dicionário {dia: valor_total} para um mês específico."""
    if df.empty:
        return {}

    mask = (
        df["data_vencimento"].notna() &
        (df["data_vencimento"].apply(lambda d: d.year if d else None) == year) &
        (df["data_vencimento"].apply(lambda d: d.month if d else None) == month) &
        (~df["status"].isin([STATUS_PAGO, STATUS_CANCELADO]))
    )

    filtered = df[mask].copy()
    if filtered.empty:
        return {}

    filtered["dia"] = filtered["data_vencimento"].apply(lambda d: d.day)
    return filtered.groupby("dia")["valor"].sum().to_dict()


def get_boletos_by_date(df: pd.DataFrame, target_date: date) -> pd.DataFrame:
    """Retorna boletos de uma data específica."""
    if df.empty:
        return df
    mask = df["data_vencimento"] == target_date
    return df[mask].sort_values("valor", ascending=False)
