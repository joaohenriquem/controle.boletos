# utils/constants.py
# Constantes globais da aplicação Bem Estar Financeiro

# Status possíveis de um boleto
STATUS_PENDENTE = "pendente"
STATUS_PAGO = "pago"
STATUS_VENCIDO = "vencido"
STATUS_CANCELADO = "cancelado"
STATUS_OPTIONS = [STATUS_PENDENTE, STATUS_PAGO, STATUS_VENCIDO, STATUS_CANCELADO]

# Colunas obrigatórias por aba
BOLETOS_COLUMNS = [
    "id", "descricao", "fornecedor", "cobrador", "categoria",
    "numero_documento", "data_emissao", "data_vencimento", "valor",
    "status", "recorrente", "observacoes", "competencia",
    "data_pagamento", "criado_em", "atualizado_em"
]

PARAMETROS_COLUMNS = ["chave", "valor"]

FORNECEDORES_COLUMNS = ["id", "nome", "ativo"]

CATEGORIAS_COLUMNS = ["id", "nome", "ativo"]

# Nomes das abas na planilha
SHEET_BOLETOS = "boletos"
SHEET_PARAMETROS = "parametros"
SHEET_FORNECEDORES = "fornecedores"
SHEET_CATEGORIAS = "categorias"

# Parâmetros padrão
DEFAULT_PARAMS = {
    "limite_maximo_diario": "15000.00",
    "dias_alerta": "3",
    "faixa_verde_percentual": "70",
    "faixa_amarela_percentual": "100",
}

# Cores da identidade visual
COLORS = {
    "primaria": "#2E8B57",
    "primaria_hover": "#256F46",
    "secundaria": "#7BC67B",
    "apoio": "#4C9CBF",
    "alerta": "#F2C94C",
    "erro": "#D64545",
    "fundo": "#F7FAF8",
    "cards": "#FFFFFF",
    "texto": "#1F2937",
    "texto_secundario": "#6B7280",
    "borda": "#D9E4DD",
}

# Cores de status
STATUS_COLORS = {
    STATUS_PENDENTE: "#F2C94C",
    STATUS_PAGO: "#2E8B57",
    STATUS_VENCIDO: "#D64545",
    STATUS_CANCELADO: "#9CA3AF",
}

# Dados iniciais (seed)
SEED_CATEGORIAS = [
    {"id": "cat-001", "nome": "Medicamentos", "ativo": "TRUE"},
    {"id": "cat-002", "nome": "Insumos", "ativo": "TRUE"},
    {"id": "cat-003", "nome": "Aluguel", "ativo": "TRUE"},
    {"id": "cat-004", "nome": "Energia Elétrica", "ativo": "TRUE"},
    {"id": "cat-005", "nome": "Água", "ativo": "TRUE"},
    {"id": "cat-006", "nome": "Internet/Telefone", "ativo": "TRUE"},
    {"id": "cat-007", "nome": "Impostos", "ativo": "TRUE"},
    {"id": "cat-008", "nome": "Folha de Pagamento", "ativo": "TRUE"},
    {"id": "cat-009", "nome": "Marketing", "ativo": "TRUE"},
    {"id": "cat-010", "nome": "Outros", "ativo": "TRUE"},
]

SEED_FORNECEDORES = [
    {"id": "forn-001", "nome": "Distribuidora Pharma BR", "ativo": "TRUE"},
    {"id": "forn-002", "nome": "Medley Farmacêutica", "ativo": "TRUE"},
    {"id": "forn-003", "nome": "EMS S/A", "ativo": "TRUE"},
    {"id": "forn-004", "nome": "Eurofarma", "ativo": "TRUE"},
    {"id": "forn-005", "nome": "CPFL Energia", "ativo": "TRUE"},
    {"id": "forn-006", "nome": "Sabesp", "ativo": "TRUE"},
    {"id": "forn-007", "nome": "Vivo Empresas", "ativo": "TRUE"},
    {"id": "forn-008", "nome": "Imobiliária Central", "ativo": "TRUE"},
    {"id": "forn-009", "nome": "Prefeitura Municipal", "ativo": "TRUE"},
    {"id": "forn-010", "nome": "Contabilidade Silva", "ativo": "TRUE"},
]

SEED_BOLETOS = [
    {
        "id": "bol-001",
        "descricao": "Lote de medicamentos genéricos - Janeiro",
        "fornecedor": "Distribuidora Pharma BR",
        "cobrador": "Distribuidora Pharma BR",
        "categoria": "Medicamentos",
        "numero_documento": "NF-2025-001234",
        "data_emissao": "2025-01-05",
        "data_vencimento": "2025-02-05",
        "valor": "8500.00",
        "status": "pago",
        "recorrente": "FALSE",
        "observacoes": "Lote mensal de genéricos",
        "competencia": "2025-01",
        "data_pagamento": "2025-02-04",
        "criado_em": "2025-01-05 10:00:00",
        "atualizado_em": "2025-02-04 09:30:00",
    },
    {
        "id": "bol-002",
        "descricao": "Aluguel do ponto comercial - Fevereiro",
        "fornecedor": "Imobiliária Central",
        "cobrador": "Imobiliária Central",
        "categoria": "Aluguel",
        "numero_documento": "ALG-2025-02",
        "data_emissao": "2025-01-20",
        "data_vencimento": "2025-02-10",
        "valor": "6200.00",
        "status": "pago",
        "recorrente": "TRUE",
        "observacoes": "Aluguel mensal do ponto",
        "competencia": "2025-02",
        "data_pagamento": "2025-02-10",
        "criado_em": "2025-01-20 08:00:00",
        "atualizado_em": "2025-02-10 11:00:00",
    },
    {
        "id": "bol-003",
        "descricao": "Conta de energia - Fevereiro",
        "fornecedor": "CPFL Energia",
        "cobrador": "CPFL Energia",
        "categoria": "Energia Elétrica",
        "numero_documento": "CPFL-2025-456",
        "data_emissao": "2025-02-01",
        "data_vencimento": "2025-02-20",
        "valor": "1850.00",
        "status": "pago",
        "recorrente": "TRUE",
        "observacoes": "",
        "competencia": "2025-02",
        "data_pagamento": "2025-02-19",
        "criado_em": "2025-02-01 07:00:00",
        "atualizado_em": "2025-02-19 14:00:00",
    },
]
