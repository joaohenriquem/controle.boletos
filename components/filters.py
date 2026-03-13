# components/filters.py
# Componentes de filtro para consulta e listagem de boletos

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from utils.dates import today, date_range_this_month, date_range_next_month


def render_quick_filters():
    """Renderiza botões de filtro rápido e retorna (data_inicio, data_fim)."""
    st.markdown("**Filtros rápidos:**")
    col1, col2, col3, col4 = st.columns(4)

    t = today()
    first_month, last_month = date_range_this_month()
    first_next, last_next = date_range_next_month()

    with col1:
        if st.button("📅 Hoje", width="stretch"):
            st.session_state["filtro_data_inicio"] = t
            st.session_state["filtro_data_fim"] = t
    with col2:
        if st.button("📆 Próx. 7 dias", width="stretch"):
            st.session_state["filtro_data_inicio"] = t
            st.session_state["filtro_data_fim"] = t + timedelta(days=7)
    with col3:
        if st.button("🗓️ Este mês", width="stretch"):
            st.session_state["filtro_data_inicio"] = first_month
            st.session_state["filtro_data_fim"] = last_month
    with col4:
        if st.button("➡️ Próx. mês", width="stretch"):
            st.session_state["filtro_data_inicio"] = first_next
            st.session_state["filtro_data_fim"] = last_next

    return (
        st.session_state.get("filtro_data_inicio", first_month),
        st.session_state.get("filtro_data_fim", last_month),
    )


def render_advanced_filters(fornecedores: list, categorias: list):
    """Renderiza filtros avançados e retorna dicionário de filtros."""
    with st.expander("🔍 Filtros avançados", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            data_inicio = st.date_input(
                "Data início",
                value=st.session_state.get("filtro_data_inicio", today().replace(day=1)),
                key="filter_date_start",
            )
            fornecedor = st.selectbox(
                "Fornecedor",
                options=["Todos"] + fornecedores,
                key="filter_fornecedor",
            )
            busca = st.text_input("🔎 Busca textual", key="filter_busca")

        with col2:
            data_fim = st.date_input(
                "Data fim",
                value=st.session_state.get("filtro_data_fim", today() + timedelta(days=30)),
                key="filter_date_end",
            )
            categoria = st.selectbox(
                "Categoria",
                options=["Todas"] + categorias,
                key="filter_categoria",
            )
            status = st.selectbox(
                "Status",
                options=["Todos", "pendente", "pago", "vencido", "cancelado"],
                key="filter_status",
            )

        col_sort1, col_sort2 = st.columns(2)
        with col_sort1:
            ordenar_por = st.selectbox(
                "Ordenar por",
                options=["data_vencimento", "valor", "descricao", "fornecedor"],
                key="filter_sort",
            )
        with col_sort2:
            ordem = st.selectbox(
                "Ordem",
                options=["Crescente", "Decrescente"],
                key="filter_order",
            )

    return {
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "fornecedor": fornecedor if fornecedor != "Todos" else None,
        "categoria": categoria if categoria != "Todas" else None,
        "status": status if status != "Todos" else None,
        "busca": busca.strip() if busca else None,
        "ordenar_por": ordenar_por,
        "ascendente": ordem == "Crescente",
    }


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Aplica filtros ao DataFrame de boletos."""
    if df.empty:
        return df

    filtered = df.copy()

    # Filtro por período
    if filters.get("data_inicio"):
        filtered = filtered[
            filtered["data_vencimento"] >= filters["data_inicio"]
        ]
    if filters.get("data_fim"):
        filtered = filtered[
            filtered["data_vencimento"] <= filters["data_fim"]
        ]

    # Filtro por fornecedor
    if filters.get("fornecedor"):
        filtered = filtered[filtered["fornecedor"] == filters["fornecedor"]]

    # Filtro por categoria
    if filters.get("categoria"):
        filtered = filtered[filtered["categoria"] == filters["categoria"]]

    # Filtro por status
    if filters.get("status"):
        filtered = filtered[filtered["status"] == filters["status"]]

    # Busca textual
    if filters.get("busca"):
        search_term = filters["busca"].lower()
        text_cols = ["descricao", "fornecedor", "cobrador", "categoria", "observacoes", "numero_documento"]
        mask = pd.Series(False, index=filtered.index)
        for col in text_cols:
            if col in filtered.columns:
                mask |= filtered[col].astype(str).str.lower().str.contains(search_term, na=False)
        filtered = filtered[mask]

    # Ordenação
    sort_col = filters.get("ordenar_por", "data_vencimento")
    ascending = filters.get("ascendente", True)
    if sort_col in filtered.columns:
        filtered = filtered.sort_values(sort_col, ascending=ascending)

    return filtered
