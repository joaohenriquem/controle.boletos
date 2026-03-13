# pages/6_Relatorios.py
# Relatórios e exportação de dados

import streamlit as st
import pandas as pd
from io import BytesIO
from services.auth_service import require_auth
from services.google_sheets_service import get_boletos, get_fornecedores_ativos, get_categorias_ativas
from services.dashboard_service import prepare_boletos_df
from components.filters import render_advanced_filters, apply_filters
from components.tables import render_boletos_table
from utils.formatters import format_currency, format_date_br

st.set_page_config(page_title="Relatórios — Bem Estar Financeiro", page_icon="📋", layout="wide")

try:
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

require_auth()

st.html("""
<div class="page-header">
    <h1>📋 Relatórios</h1>
    <p>Exporte e analise seus dados financeiros</p>
</div>
""")

# Carregar dados
with st.spinner("Carregando dados..."):
    df_raw = get_boletos()
    df = prepare_boletos_df(df_raw)
    fornecedores = get_fornecedores_ativos()
    categorias = get_categorias_ativas()

# Filtros
filters = render_advanced_filters(fornecedores, categorias)
filtered = apply_filters(df, filters)

st.markdown(f"### Relatório — {len(filtered)} boleto(s)")

# Tabela analítica
render_boletos_table(filtered)

# Resumo por status
if not filtered.empty:
    st.markdown("### Resumo")

    col1, col2, col3 = st.columns(3)
    with col1:
        pendentes = filtered[filtered["status"] == "pendente"]
        st.metric("Pendentes", f"{len(pendentes)}", f"{format_currency(pendentes['valor'].sum())}")
    with col2:
        pagos = filtered[filtered["status"] == "pago"]
        st.metric("Pagos", f"{len(pagos)}", f"{format_currency(pagos['valor'].sum())}")
    with col3:
        vencidos = filtered[filtered["status"] == "vencido"]
        st.metric("Vencidos", f"{len(vencidos)}", f"{format_currency(vencidos['valor'].sum())}")

# Exportações
st.markdown("### 📥 Exportar Dados")
col_exp1, col_exp2 = st.columns(2)

with col_exp1:
    # CSV
    if not filtered.empty:
        export_df = filtered.copy()
        # Formatar para exportação
        if "data_vencimento" in export_df.columns:
            export_df["data_vencimento"] = export_df["data_vencimento"].apply(
                lambda d: format_date_br(d) if pd.notna(d) else ""
            )
        if "data_emissao" in export_df.columns:
            export_df["data_emissao"] = export_df["data_emissao"].apply(
                lambda d: format_date_br(d) if pd.notna(d) else ""
            )

        csv = export_df.to_csv(index=False, sep=";", encoding="utf-8-sig")
        st.download_button(
            "📄 Baixar CSV",
            data=csv,
            file_name="relatorio_boletos.csv",
            mime="text/csv",
            width="stretch",
        )
    else:
        st.info("Nenhum dado para exportar.")

with col_exp2:
    # Excel
    if not filtered.empty:
        try:
            buffer = BytesIO()
            export_df = filtered.copy()
            if "data_vencimento" in export_df.columns:
                export_df["data_vencimento"] = export_df["data_vencimento"].apply(
                    lambda d: format_date_br(d) if pd.notna(d) else ""
                )
            if "data_emissao" in export_df.columns:
                export_df["data_emissao"] = export_df["data_emissao"].apply(
                    lambda d: format_date_br(d) if pd.notna(d) else ""
                )

            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                export_df.to_excel(writer, index=False, sheet_name="Boletos")

            st.download_button(
                "📊 Baixar Excel",
                data=buffer.getvalue(),
                file_name="relatorio_boletos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
        except ImportError:
            st.warning("Exportação Excel não disponível. Use CSV.")
    else:
        st.info("Nenhum dado para exportar.")
