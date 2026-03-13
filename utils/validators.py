# utils/validators.py
# Funções de validação para formulários e dados de boletos

from datetime import date, datetime
from utils.formatters import parse_currency


def validate_boleto_form(data: dict) -> list:
    """
    Valida os campos de um formulário de boleto.
    Retorna lista de erros. Lista vazia = válido.
    """
    errors = []

    if not data.get("descricao", "").strip():
        errors.append("Descrição é obrigatória.")

    if not data.get("fornecedor", "").strip():
        errors.append("Fornecedor é obrigatório.")

    if not data.get("categoria", "").strip():
        errors.append("Categoria é obrigatória.")

    # Validar valor
    try:
        v_raw = data.get("valor", 0)
        valor = parse_currency(v_raw)
        if valor <= 0:
            errors.append(f"Valor deve ser maior que zero. (Recebido: {v_raw})")
    except (ValueError, TypeError):
        errors.append("Valor inválido.")

    # Validar data de vencimento
    dv = data.get("data_vencimento")
    if not dv:
        errors.append("Data de vencimento é obrigatória.")

    # Validar data de emissão
    de = data.get("data_emissao")
    if not de:
        errors.append("Data de emissão é obrigatória.")

    # Validar coerência de datas
    if dv and de:
        try:
            if isinstance(de, str):
                de = datetime.strptime(de, "%Y-%m-%d").date()
            if isinstance(dv, str):
                dv = datetime.strptime(dv, "%Y-%m-%d").date()
            if de > dv:
                errors.append("Data de emissão não pode ser posterior à data de vencimento.")
        except (ValueError, TypeError):
            pass

    return errors


def validate_required(value, field_name: str) -> str | None:
    """Valida se um campo obrigatório foi preenchido."""
    if not value or (isinstance(value, str) and not value.strip()):
        return f"{field_name} é obrigatório(a)."
    return None


def validate_positive_number(value, field_name: str) -> str | None:
    """Valida se é um número positivo."""
    try:
        if float(value) <= 0:
            return f"{field_name} deve ser maior que zero."
    except (ValueError, TypeError):
        return f"{field_name} deve ser um número válido."
    return None
