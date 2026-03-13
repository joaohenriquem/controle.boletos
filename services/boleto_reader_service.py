# services/boleto_reader_service.py
# Serviço de leitura automática de boletos (PDF e imagem)

import re
from datetime import datetime
from io import BytesIO


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extrai texto de um arquivo PDF usando pdfplumber."""
    try:
        import pdfplumber
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
    except Exception:
        # Fallback com pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(file_bytes))
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception:
            return ""


def extract_text_from_image(file_bytes: bytes) -> str:
    """
    Tenta extrair texto de uma imagem.
    Como OCR pesado não é viável no Streamlit Cloud,
    retorna string vazia e avisa o usuário.
    """
    # OCR leve não está disponível por padrão no Streamlit Cloud
    # Retornamos vazio para que a UI informe ao usuário
    return ""


def parse_valor(text: str) -> str | None:
    """
    Tenta extrair valor monetário no padrão brasileiro.
    Procura padrões como: R$ 1.234,56 ou 1234,56 ou 1.234.567,89
    """
    patterns = [
        # R$ 1.234,56 ou R$1.234,56
        r'R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})',
        # Valor do documento / Valor cobrado seguido de número
        r'(?:valor|total|cobrado|documento)[:\s]*R?\$?\s*(\d{1,3}(?:\.\d{3})*,\d{2})',
        # Número com formato brasileiro sem R$
        r'(\d{1,3}(?:\.\d{3})+,\d{2})',
        # Formato simples: 1234,56
        r'(\d{4,},\d{2})',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Pegar o maior valor encontrado (geralmente é o total)
            values = []
            for m in matches:
                try:
                    cleaned = m.replace(".", "").replace(",", ".")
                    values.append(float(cleaned))
                except ValueError:
                    continue
            if values:
                max_val = max(values)
                # Formatar de volta para padrão de exibição
                return f"{max_val:.2f}"

    return None


def parse_data_vencimento(text: str) -> str | None:
    """
    Tenta extrair data de vencimento do texto do boleto.
    Procura padrões comuns de boleto bancário brasileiro.
    """
    # Padrões de data associados a vencimento
    venc_patterns = [
        r'(?:vencimento|venc\.|dt\.?\s*venc)[:\s]*(\d{2}[\/\.\-]\d{2}[\/\.\-]\d{2,4})',
        r'(\d{2}[\/\.\-]\d{2}[\/\.\-]\d{4})(?:\s*(?:venc|vencimento))?',
    ]

    for pattern in venc_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in matches:
                date_str = match.replace(".", "/").replace("-", "/")
                # Tentar parsear a data
                for fmt in ["%d/%m/%Y", "%d/%m/%y"]:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        continue

    # Fallback: buscar qualquer data no texto
    generic = re.findall(r'(\d{2}/\d{2}/\d{4})', text)
    if generic:
        for date_str in generic:
            try:
                dt = datetime.strptime(date_str, "%d/%m/%Y")
                # Ignorar datas muito antigas (provavelmente não é vencimento)
                if dt.year >= 2020:
                    return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

    return None


def parse_cobrador(text: str) -> str | None:
    """
    Tenta extrair o nome do cobrador/beneficiário/cedente do boleto.
    """
    patterns = [
        r'(?:benefici[áa]rio|cedente|cobrador|favorecido|pagamento a)[:\s]*([A-ZÀ-Ú][A-ZÀ-Ú\s\.&\-]+)',
        r'(?:raz[ãa]o social)[:\s]*([A-ZÀ-Ú][A-ZÀ-Ú\s\.&\-]+)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            name = matches[0].strip()
            # Limpar e truncar
            name = re.sub(r'\s+', ' ', name)
            if len(name) > 3:  # Nome minimamente válido
                return name[:100]

    return None


def read_boleto(file_bytes: bytes, file_type: str) -> dict:
    """
    Lê um arquivo de boleto e tenta extrair campos relevantes.

    Retorna dict com:
        - cobrador: str ou None
        - data_vencimento: str (YYYY-MM-DD) ou None
        - valor: str ou None
        - raw_text: str (texto extraído)
        - success: bool
        - message: str
    """
    result = {
        "cobrador": None,
        "data_vencimento": None,
        "valor": None,
        "raw_text": "",
        "success": False,
        "message": "",
    }

    # Extrair texto
    if file_type == "pdf":
        text = extract_text_from_pdf(file_bytes)
    elif file_type in ("png", "jpg", "jpeg"):
        text = extract_text_from_image(file_bytes)
    else:
        result["message"] = "Formato de arquivo não suportado. Envie PDF ou imagem."
        return result

    result["raw_text"] = text

    if not text.strip():
        if file_type in ("png", "jpg", "jpeg"):
            result["message"] = (
                "Não foi possível extrair texto da imagem. "
                "A leitura de imagens requer OCR, que não está disponível neste ambiente. "
                "Tente enviar o boleto em PDF com texto selecionável."
            )
        else:
            result["message"] = (
                "Não foi possível extrair texto do PDF. "
                "O arquivo pode ser uma imagem escaneada. "
                "Complete os dados manualmente."
            )
        return result

    # Tentar parsing dos campos
    result["valor"] = parse_valor(text)
    result["data_vencimento"] = parse_data_vencimento(text)
    result["cobrador"] = parse_cobrador(text)

    # Avaliar resultado
    found = sum([
        1 for v in [result["valor"], result["data_vencimento"], result["cobrador"]]
        if v is not None
    ])

    if found == 3:
        result["success"] = True
        result["message"] = "Boleto lido com sucesso. Revise os dados antes de salvar."
    elif found > 0:
        result["success"] = True
        result["message"] = (
            "Não foi possível identificar todos os campos. "
            "Complete manualmente os dados ausentes."
        )
    else:
        result["message"] = (
            "Não foi possível identificar os campos do boleto. "
            "Preencha os dados manualmente."
        )

    return result
