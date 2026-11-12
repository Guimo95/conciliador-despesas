"""Importadores: OFX (extrato ou fatura de qualquer banco), CSV com perfil de colunas e transações da Belvo.
Todos devolvem dicts no formato do livro-razão, com valor positivo para despesa e tipo 'saida' ou 'entrada'."""
import csv
import json
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path


def _decimal_br_ou_us(texto: str) -> Decimal:
    t = texto.strip().replace("R$", "").replace(" ", "")
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".") if t.rfind(",") > t.rfind(".") else t.replace(",", "")
    elif "," in t:
        t = t.replace(",", ".")
    return Decimal(t)


def ler_ofx(caminho, conta="") -> list:
    """OFX 1.x (SGML) ou 2.x (XML): lê cada STMTTRN. Débito vira despesa (valor positivo)."""
    texto = Path(caminho).read_bytes().decode("latin-1", errors="replace")
    resultado = []
    for bloco in re.findall(r"<STMTTRN>(.*?)(?:</STMTTRN>|(?=<STMTTRN>)|</BANKTRANLIST>)", texto, flags=re.S | re.I):
        def campo(nome):
            m = re.search(rf"<{nome}>([^<\r\n]*)", bloco, flags=re.I)
            return m.group(1).strip() if m else ""
        valor = _decimal_br_ou_us(campo("TRNAMT"))
        data = datetime.strptime(campo("DTPOSTED")[:8], "%Y%m%d").date().isoformat()
        descricao = campo("MEMO") or campo("NAME")
        resultado.append({"data": data, "descricao_banco": descricao, "valor": f"{abs(valor):.2f}",
                          "tipo": "saida" if valor < 0 else "entrada", "origem": "ofx", "conta": conta, "parcela": ""})
    return resultado


def ler_csv_banco(caminho, perfil: dict, conta="") -> list:
    """CSV exportado pelo banco. O perfil diz as colunas: data, descricao, valor, formato_data,
    separador, parcela (opcional) e se despesa vem negativa (despesa_negativa: true) ou positiva (fatura)."""
    resultado = []
    with open(caminho, encoding=perfil.get("codificacao", "utf-8-sig"), newline="") as f:
        for linha in csv.DictReader(f, delimiter=perfil.get("separador", ";")):
            valor = _decimal_br_ou_us(linha[perfil["valor"]])
            negativa = perfil.get("despesa_negativa", True)
            saida = valor < 0 if negativa else valor > 0
            data = datetime.strptime(linha[perfil["data"]].strip(), perfil.get("formato_data", "%d/%m/%Y")).date()
            parcela = linha.get(perfil.get("parcela", ""), "") or ""
            resultado.append({"data": data.isoformat(), "descricao_banco": linha[perfil["descricao"]].strip(),
                              "valor": f"{abs(valor):.2f}", "tipo": "saida" if saida else "entrada",
                              "origem": "csv", "conta": conta, "parcela": "" if parcela.lower().startswith("única") else parcela})
    return resultado


def ler_belvo(caminho, conta="") -> list:
    """Transações que o agente salvou da Belvo (lista JSON). O valor em reais fica em local_currency_amount
    (amount é a moeda original). type OUTFLOW = despesa, INFLOW = entrada ou estorno."""
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    resultado = []
    for t in dados:
        valor = Decimal(str(t.get("local_currency_amount", t.get("amount"))))
        parcela = str(t.get("parcela") or "")  # o agente preenche "2/10" quando a Belvo indica compra parcelada
        resultado.append({"data": (t.get("value_date") or t.get("accounting_date"))[:10],
                          "descricao_banco": (t.get("description") or "").strip(), "valor": f"{abs(valor):.2f}",
                          "tipo": "saida" if t.get("type") == "OUTFLOW" else "entrada", "origem": "belvo",
                          "conta": conta or (t.get("account") or {}).get("name", ""), "parcela": parcela})
    return resultado
