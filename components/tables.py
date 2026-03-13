# components/tables.py
# Componentes de tabela para exibição de boletos

import streamlit as st
import pandas as pd
from utils.formatters import format_currency, format_date_br, status_emoji
from components.cards import render_status_badge


def render_boletos_table(df: pd.DataFrame, show_actions: bool = False):
    """Renderiza tabela de boletos com formatação profissional."""
    if df.empty:
        st.info("📭 Nenhum boleto encontrado com os filtros selecionados.")
        return

    # Preparar dados para exibição
    display_df = df.copy()

    # Formatar colunas
    if "valor" in display_df.columns:
        display_df["valor_fmt"] = display_df["valor"].apply(
            lambda v: format_currency(v) if pd.notna(v) else "—"
        )
    if "data_vencimento" in display_df.columns:
        display_df["vencimento_fmt"] = display_df["data_vencimento"].apply(
            lambda d: format_date_br(d) if pd.notna(d) else "—"
        )
    if "status" in display_df.columns:
        display_df["status_fmt"] = display_df["status"].apply(
            lambda s: f"{status_emoji(s)} {s.capitalize()}"
        )

    # Selecionar colunas para exibição
    cols_display = {
        "descricao": "Descrição",
        "fornecedor": "Fornecedor",
        "categoria": "Categoria",
        "vencimento_fmt": "Vencimento",
        "valor_fmt": "Valor",
        "status_fmt": "Status",
    }

    available_cols = [c for c in cols_display.keys() if c in display_df.columns]
    rename_map = {c: cols_display[c] for c in available_cols}

    table_df = display_df[available_cols].rename(columns=rename_map)

    st.dataframe(
        table_df,
        width="stretch",
        hide_index=True,
        height=min(400, 40 + len(table_df) * 35),
    )

    # Resumo
    total = df["valor"].sum() if "valor" in df.columns else 0
    st.markdown(
        f"<div style='text-align:right; padding:0.5rem; color:#6B7280;'>"
        f"<strong>{len(df)}</strong> boleto(s) — Total: <strong>{format_currency(total)}</strong>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_boleto_detail(boleto: pd.Series):
    """Renderiza detalhes de um boleto em formato de card."""
    st.html(f"""
    <div style="
        background: white;
        border: 1px solid #D9E4DD;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
    ">
        <h4 style="color:#1F2937; margin-bottom:1rem;">
            {boleto.get('descricao', 'Sem descrição')}
        </h4>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.75rem;">
            <div><strong>Fornecedor:</strong> {boleto.get('fornecedor', '—')}</div>
            <div><strong>Cobrador:</strong> {boleto.get('cobrador', '—')}</div>
            <div><strong>Categoria:</strong> {boleto.get('categoria', '—')}</div>
            <div><strong>Nº Documento:</strong> {boleto.get('numero_documento', '—')}</div>
            <div><strong>Emissão:</strong> {format_date_br(boleto.get('data_emissao', ''))}</div>
            <div><strong>Vencimento:</strong> {format_date_br(boleto.get('data_vencimento', ''))}</div>
            <div><strong>Valor:</strong> <span style="font-size:1.1rem; font-weight:700;">
                {format_currency(boleto.get('valor', 0))}</span></div>
            <div><strong>Status:</strong> {render_status_badge(boleto.get('status', 'pendente'))}</div>
        </div>
        {"<div style='margin-top:0.75rem;'><strong>Observações:</strong> " + str(boleto.get('observacoes', '')) + "</div>" if boleto.get('observacoes') else ""}
    </div>
    """)
