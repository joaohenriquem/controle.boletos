# services/previsao_service.py
# Lógica de previsão financeira e projeções

import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from utils.dates import today, months_ahead
from utils.constants import STATUS_PAGO, STATUS_CANCELADO


def previsao_mensal(df: pd.DataFrame, meses: int = 6) -> pd.DataFrame:
    """
    Gera previsão de valores por mês para os próximos N meses.
    Baseia-se nos boletos pendentes/vencidos com data futura.
    """
    if df.empty:
        return pd.DataFrame(columns=["ano", "mes", "total"])

    periods = months_ahead(meses)
    result = []

    for year, month in periods:
        mask = (
            df["data_vencimento"].notna() &
            (df["data_vencimento"].apply(lambda d: d.year if d else None) == year) &
            (df["data_vencimento"].apply(lambda d: d.month if d else None) == month) &
            (~df["status"].isin([STATUS_PAGO, STATUS_CANCELADO]))
        )
        total = df.loc[mask, "valor"].sum()
        result.append({"ano": year, "mes": month, "total": total})

    return pd.DataFrame(result)


def previsao_semanal(df: pd.DataFrame, semanas: int = 4) -> pd.DataFrame:
    """Gera previsão semanal para as próximas N semanas."""
    if df.empty:
        return pd.DataFrame(columns=["semana", "inicio", "fim", "total"])

    t = today()
    result = []

    for i in range(semanas):
        inicio = t + pd.Timedelta(weeks=i)
        fim = inicio + pd.Timedelta(days=6)

        mask = (
            df["data_vencimento"].notna() &
            (df["data_vencimento"] >= inicio) &
            (df["data_vencimento"] <= fim) &
            (~df["status"].isin([STATUS_PAGO, STATUS_CANCELADO]))
        )
        total = df.loc[mask, "valor"].sum()
        result.append({
            "semana": f"Semana {i + 1}",
            "inicio": inicio,
            "fim": fim,
            "total": total,
        })

    return pd.DataFrame(result)


def concentracao_por_dia_mes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa boletos pendentes/vencidos por dia do mês (1-31)
    para identificar concentração de vencimentos.
    """
    if df.empty:
        return pd.DataFrame(columns=["dia_mes", "total", "qtd"])

    mask = (
        df["data_vencimento"].notna() &
        (~df["status"].isin([STATUS_PAGO, STATUS_CANCELADO]))
    )
    filtered = df[mask].copy()
    if filtered.empty:
        return pd.DataFrame(columns=["dia_mes", "total", "qtd"])

    filtered["dia_mes"] = filtered["data_vencimento"].apply(lambda d: d.day)
    grouped = filtered.groupby("dia_mes").agg(
        total=("valor", "sum"),
        qtd=("id", "count"),
    ).reset_index()

    return grouped.sort_values("dia_mes")


def totais_por_categoria(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa valores por categoria."""
    if df.empty:
        return pd.DataFrame(columns=["categoria", "total"])

    mask = ~df["status"].isin([STATUS_CANCELADO])
    filtered = df[mask]
    if filtered.empty:
        return pd.DataFrame(columns=["categoria", "total"])

    return filtered.groupby("categoria")["valor"].sum().reset_index().rename(
        columns={"valor": "total"}
    ).sort_values("total", ascending=False)


def totais_por_status(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa valores por status."""
    if df.empty:
        return pd.DataFrame(columns=["status", "total", "qtd"])

    grouped = df.groupby("status").agg(
        total=("valor", "sum"),
        qtd=("id", "count"),
    ).reset_index()

    return grouped
