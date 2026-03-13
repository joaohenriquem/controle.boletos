# 🌿 Bem Estar Financeiro

**Controle inteligente de vencimentos e previsões** — Farmácia Bem Estar

Uma aplicação completa para gestão financeira de boletos, desenvolvida com Streamlit + Google Sheets, pronta para deploy no Streamlit Community Cloud.

---

## ✨ Funcionalidades

- **Dashboard** com KPIs em tempo real (vencimentos do dia, vencidos, previsões)
- **Cadastro de boletos** com validação completa e geração de ID único
- **Leitura automática de boletos** via PDF (extração de valor, vencimento e cobrador)
- **Consulta avançada** com filtros por período, fornecedor, categoria, status e busca textual
- **Calendário financeiro** com visão mensal e destaque visual de dias críticos
- **Parametrização** de limite diário, faixas de risco, fornecedores e categorias
- **Relatórios** com exportação em CSV e Excel
- **Gráficos Plotly** — barras, linhas, rosca, concentração de vencimentos
- **Login com Google** — acesso restrito a e-mails autorizados
- **Persistência em Google Sheets** — sem banco de dados, 100% cloud

---

## 🏗️ Estrutura do Projeto

```
bem_estar_financeiro/
├── app.py                          # Ponto de entrada
├── auth.py                         # Componente de login/logout na sidebar
├── requirements.txt                # Dependências
├── .gitignore
├── README.md
├── .streamlit/
│   └── secrets.toml.example        # Exemplo de configuração
├── assets/
│   ├── logo.png                    # Logo (adicione a sua)
│   └── styles.css                  # CSS customizado
├── components/
│   ├── cards.py                    # KPI cards e alertas
│   ├── charts.py                   # Gráficos Plotly
│   ├── filters.py                  # Filtros e busca
│   └── tables.py                   # Tabelas de boletos
├── pages/
│   ├── 1_Dashboard.py
│   ├── 2_Cadastro_de_Boletos.py
│   ├── 3_Consulta.py
│   ├── 4_Calendario.py
│   ├── 5_Parametros.py
│   └── 6_Relatorios.py
├── services/
│   ├── auth_service.py             # Lógica de autenticação OAuth
│   ├── google_sheets_service.py    # Camada de persistência
│   ├── dashboard_service.py        # Lógica de KPIs
│   ├── previsao_service.py         # Projeções financeiras
│   └── boleto_reader_service.py    # Leitura automática de PDFs
└── utils/
    ├── constants.py                # Constantes, cores, seeds
    ├── formatters.py               # Formatação de moeda e datas
    ├── validators.py               # Validação de formulários
    └── dates.py                    # Funções auxiliares de data
```

---

## 🚀 Execução Local

### 1. Clonar e criar ambiente virtual

```bash
git clone https://github.com/joaohenriquem/controle.boletos.git
cd controle.boletos

python -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### 2. Configurar secrets

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edite o arquivo `.streamlit/secrets.toml` com suas credenciais (veja seções abaixo).

### 3. Rodar a aplicação

```bash
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`.

---

## 🔐 Configuração do Google Login (OAuth)

### Passo a passo

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto (ou use um existente)
3. Vá em **APIs e Serviços → Tela de Consentimento OAuth**
   - Configure como "Externo"
   - Preencha nome, e-mail, etc.
   - Adicione os escopos: `openid`, `email`, `profile`
4. Vá em **APIs e Serviços → Credenciais**
   - Clique em **Criar credenciais → ID do cliente OAuth**
   - Tipo: **Aplicativo da Web**
   - URIs de redirecionamento autorizados:
     - Local: `http://localhost:8501/oauth2callback`
     - Produção: `https://sua-app.streamlit.app/oauth2callback`
5. Copie o `client_id` e `client_secret`

### Configurar no secrets.toml

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "uma-string-aleatoria-segura"
client_id = "SEU_CLIENT_ID.apps.googleusercontent.com"
client_secret = "SEU_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

> **Importante:** No Streamlit Community Cloud, altere o `redirect_uri` para o URL da sua app (ex: `https://sua-app.streamlit.app/oauth2callback`).

---

## 📊 Configuração do Google Sheets

### Criar Service Account

1. No Google Cloud Console, vá em **IAM e Admin → Contas de serviço**
2. Clique em **Criar conta de serviço**
3. Dê um nome (ex: `bem-estar-sheets`)
4. Clique em **Criar e continuar** (pule as permissões opcionais)
5. Na lista de contas de serviço, clique nos 3 pontos → **Gerenciar chaves**
6. Adicione chave → Criar nova chave → JSON
7. Um arquivo JSON será baixado

### Criar e compartilhar a planilha

1. Crie uma planilha no Google Sheets chamada **"Bem Estar Financeiro"** (ou o nome que preferir)
2. Compartilhe a planilha com o e-mail da service account (encontrado no JSON, campo `client_email`) — dê permissão de **Editor**

### Configurar no secrets.toml

Copie os campos do JSON para o `secrets.toml`:

```toml
[google_service_account]
type = "service_account"
project_id = "seu-projeto"
private_key_id = "abc123..."
private_key = "-----BEGIN PRIVATE KEY-----\nSUA_CHAVE\n-----END PRIVATE KEY-----\n"
client_email = "bem-estar-sheets@seu-projeto.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

> **Dica:** A `private_key` deve manter os `\n` literais (não quebras de linha reais) no formato TOML.

### Configurar nome da planilha e e-mails

```toml
[app]
spreadsheet_name = "Bem Estar Financeiro"
allowed_emails = ["joao@empresa.com", "maria@empresa.com"]
```

---

## ☁️ Deploy no Streamlit Community Cloud

### 1. Subir no GitHub

```bash
git init
git add .
git commit -m "Bem Estar Financeiro - versão inicial"
git remote add origin https://github.com/joaohenriquem/controle.boletos.git
git push -u origin main
```

### 2. Conectar no Streamlit Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Clique em **New app**
3. Selecione o repositório, branch `main` e arquivo `app.py`

### 3. Configurar Secrets no painel

1. Na página da app no Streamlit Cloud, vá em **Settings → Secrets**
2. Cole o conteúdo completo do seu `secrets.toml`
3. Salve

### 4. Publicar

A app será buildada e publicada automaticamente. Lembre-se de atualizar o `redirect_uri` no Google Cloud Console e nos secrets para o URL da app publicada.

---

## 📋 Estrutura da Planilha

A aplicação cria automaticamente as abas necessárias na primeira execução:

### Aba `boletos`
| Coluna | Descrição |
|--------|-----------|
| id | UUID único |
| descricao | Descrição do boleto |
| fornecedor | Nome do fornecedor |
| cobrador | Beneficiário/cobrador |
| categoria | Categoria do gasto |
| numero_documento | Nº do documento/NF |
| data_emissao | Data de emissão (YYYY-MM-DD) |
| data_vencimento | Data de vencimento (YYYY-MM-DD) |
| valor | Valor numérico |
| status | pendente / pago / vencido / cancelado |
| recorrente | TRUE / FALSE |
| observacoes | Texto livre |
| competencia | Mês de competência (YYYY-MM) |
| data_pagamento | Data em que foi pago |
| criado_em | Timestamp de criação |
| atualizado_em | Timestamp de atualização |

### Aba `parametros`
| Chave | Descrição |
|-------|-----------|
| limite_maximo_diario | Valor máximo de pagamentos por dia |
| dias_alerta | Dias de antecedência para alertas |
| faixa_verde_percentual | Limite % para faixa verde |
| faixa_amarela_percentual | Limite % para faixa amarela |

### Aba `fornecedores`
| Coluna | Descrição |
|--------|-----------|
| id | UUID do fornecedor |
| nome | Nome |
| ativo | TRUE / FALSE |

### Aba `categorias`
| Coluna | Descrição |
|--------|-----------|
| id | UUID da categoria |
| nome | Nome |
| ativo | TRUE / FALSE |

---

## 🔮 Roadmap Futuro

- [ ] Importação em massa via Excel/CSV
- [ ] Recorrência automática (gerar boletos mensais automaticamente)
- [ ] Múltiplos usuários com perfis de acesso (admin, operador, visualizador)
- [ ] Migração para banco relacional (PostgreSQL/Supabase)
- [ ] Auditoria de ações (log de quem criou/editou/excluiu)
- [ ] Upload e anexo de comprovantes de pagamento
- [ ] Notificações por e-mail para boletos próximos do vencimento
- [ ] Dashboard comparativo mês a mês
- [ ] Integração com APIs bancárias para leitura automática
- [ ] App mobile (PWA)

---

## 📄 Licença

Uso interno — Farmácia Bem Estar.
