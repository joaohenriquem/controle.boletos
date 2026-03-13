# pages/7_Como_Usar.py
# Guia de utilização e documentação passo a passo

import streamlit as st
from services.auth_service import require_auth
from utils.constants import COLORS

st.set_page_config(page_title="Guia de Uso — Bem Estar Financeiro", page_icon="📖", layout="wide")

# Carregar CSS
try:
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

require_auth()

# CSS Extra para a página de guia
st.markdown(f"""
<style>
    .guide-card {{
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid {COLORS['borda']};
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }}
    .step-number {{
        background: {COLORS['primaria']};
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 10px;
    }}
    .highlight-box {{
        background: #F0F9FF;
        border-left: 4px solid {COLORS['apoio']};
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }}
    .status-dot {{
        height: 12px;
        width: 12px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 5px;
    }}
</style>
""", unsafe_allow_html=True)

st.html("""
<div class="page-header">
    <h1>📖 Como Usar o Sistema</h1>
    <p>Aprenda a gerenciar as finanças da Farmácia Bem Estar passo a passo</p>
</div>
""")

# Introdução
st.markdown("""
Bem-vindo ao seu novo painel financeiro! Este sistema foi projetado para ser intuitivo e eficiente. 
Abaixo, você encontrará o guia detalhado de cada módulo.
""")

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    # SEÇÃO 1: DASHBOARD
    with st.expander("📊 1. Dashboard: Visão Geral", expanded=True):
        st.markdown(f"""
        O **Dashboard** é sua central de controle. Aqui você vê a saúde financeira do dia e do mês.
        
        <div class="highlight-box">
            <strong>O que observar:</strong><br>
            • <b>KPIs Superiores:</b> Quantidade e valor de boletos para hoje, vencidos e a vencer.<br>
            • <b>Barra de Limite:</b> Monitora quanto do "Limite Máximo Diário" já foi comprometido hoje.
        </div>
        
        - **Cores da Barra:**
            - <span class="status-dot" style="background:{COLORS['primaria']}"></span> **Verde:** Até 70% do limite. Situação confortável.
            - <span class="status-dot" style="background:{COLORS['alerta']}"></span> **Amarelo:** Entre 70% e 100%. Ponto de atenção.
            - <span class="status-dot" style="background:{COLORS['erro']}"></span> **Vermelho:** Acima do limite. Avalie adiar pagamentos.
        """, unsafe_allow_html=True)

    # SEÇÃO 2: CALENDÁRIO
    with st.expander("📅 2. Calendário Financeiro", expanded=False):
        st.markdown(f"""
        Visualize seus vencimentos de forma espacial e organizada por cores.
        
        - **Como interagir:** 
          Dê um clique em qualquer dia do mês para abrir o detalhamento lateral.
        - **Significado das Cores nos Dias:**
            - **Cinza:** Sem boletos para o dia.
            - **Verde/Amarelo/Vermelho:** Dias pintados conforme o comprometimento do limite.
        
        <div class="highlight-box">
            <strong>Dica:</strong> Use as setas no topo para navegar entre os meses e planejar o fluxo de caixa futuro.
        </div>
        """, unsafe_allow_html=True)

with col_right:
    # SEÇÃO 3: CADASTRO E EDIÇÃO
    with st.expander("📝 3. Cadastro e Gestão de Boletos", expanded=True):
        st.markdown(f"""
        O coração dos dados. Sempre mantenha o cadastro atualizado.
        
        - <span class="step-number">1</span> **Novo Boleto:** Clique em "Novo Boleto", preencha os dados e salve.
        - <span class="step-number">2</span> **Formatação de Valor:** Você pode digitar o valor no formato brasileiro (ex: `150,00` ou `1.234,56`). O sistema entende a vírgula naturalmente.
        - <span class="step-number">3</span> **Ações Diversas:** Na tabela de registros, você pode **Editar**, **Pagar** (marcar como pago) ou **Excluir**.
        
        <div class="highlight-box" style="border-left-color: {COLORS['primaria']}">
            <strong>Sincronização:</strong> Após salvar, a página recarrega e os gráficos do Dashboard e do Calendário são atualizados automaticamente na hora!
        </div>
        """, unsafe_allow_html=True)

    # SEÇÃO 4: PARÂMETROS
    with st.expander("⚙️ 4. Configuração de Parâmetros", expanded=False):
        st.markdown(f"""
        Ajuste as "regras do jogo" da aplicação.
        
        - **Limite Máximo Diário:** O valor total que você deseja pagar por dia antes do sistema emitir alertas.
        - **Dias de Alerta:** Quantos dias antes do vencimento um boleto deve começar a aparecer nos alertas de "Próximos 7 dias".
        - **Faixas de Risco:** Defina os percentuais (X% até Verde, Y% até Amarelo).
        
        <div class="highlight-box" style="border-left-color: {COLORS['alerta']}">
            <strong>Importante:</strong> Ao clicar em "Salvar Parâmetros", o sistema atualiza a planilha no Google e limpa o cache para que a mudança valha imediatamente em todas as telas.
        </div>
        """, unsafe_allow_html=True)

st.divider()

# Rodapé de Melhores Práticas
st.markdown(f"""
<div style="text-align: center; color: {COLORS['texto_secundario']}; padding: 1rem;">
    <h4>💡 Melhores Práticas</h4>
    <p>1. Sempre marque os boletos como <b>PAGO</b> assim que quitados para limpar os KPIS de vencidos.</p>
    <p>2. Use o campo de <b>Observações</b> para registrar números de protocolo ou detalhes de negociação.</p>
    <p>3. Revise o <b>Cálculo de Previsão</b> no final de cada mês para garantir o saldo em conta.</p>
</div>
""", unsafe_allow_html=True)
