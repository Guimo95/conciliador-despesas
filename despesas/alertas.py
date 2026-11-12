"""Alertas de contas fixas: vencida, a vencer e paga em dobro. Lê meus-dados/contas.yaml.

contas:
  - {nome: Aluguel, padrao: "ALUGUEL", dia: 5, valor: 2200, aviso_dias: 3}

"padrao" é uma expressão regular procurada na descrição do banco. "valor" é opcional: se vier, o pagamento
precisa estar a até 15% dele (conta de luz varia, aluguel não).
"""
import calendar
import re
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import yaml

JANELA_ANTES = 10      # pagamento até 10 dias antes do vencimento conta como pago
TOLERANCIA = Decimal("0.15")
DIAS_DUPLICADO = 7


def carregar_contas(caminho) -> list:
    p = Path(caminho)
    if not p.exists():
        return []
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("contas", [])


def _vencimento(ano, mes, dia):
    return date(ano, mes, min(int(dia), calendar.monthrange(ano, mes)[1]))


def _casa(conta, l):
    if l.get("tipo", "saida") != "saida" or l.get("status") == "ignorado":
        return False
    if not re.search(conta["padrao"], l["descricao_banco"], flags=re.IGNORECASE):
        return False
    if conta.get("valor"):
        esperado = Decimal(str(conta["valor"]))
        return abs(Decimal(l["valor"]) - esperado) <= esperado * TOLERANCIA
    return True


def verificar(contas: list, livro: list, hoje: date) -> list:
    """Uma linha por conta: situacao = paga | a_vencer | vencida | ok, com o vencimento do mês corrente."""
    resultado = []
    for c in contas:
        venc = _vencimento(hoje.year, hoje.month, c["dia"])
        inicio = venc - timedelta(days=JANELA_ANTES)
        pagos = [l for l in livro if _casa(c, l) and inicio <= date.fromisoformat(l["data"]) <= max(hoje, venc)]
        aviso = int(c.get("aviso_dias", 3))
        if pagos:
            situacao = "paga"
        elif hoje > venc:
            situacao = "vencida"
        elif (venc - hoje).days <= aviso:
            situacao = "a_vencer"
        else:
            situacao = "ok"
        resultado.append({"nome": c["nome"], "vencimento": venc.isoformat(), "situacao": situacao,
                          "pago_em": pagos[0]["data"] if pagos else "", "valor_pago": pagos[0]["valor"] if pagos else ""})
    return resultado


def duplicados(contas: list, livro: list, hoje: date, dias_olhar=40) -> list:
    """Mesma conta, mesmo valor, paga duas vezes em até 7 dias (só nos últimos 40 dias)."""
    achados = []
    limite = hoje - timedelta(days=dias_olhar)
    for c in contas:
        pagos = sorted((l for l in livro if _casa(c, l) and date.fromisoformat(l["data"]) >= limite), key=lambda l: l["data"])
        for a, b in zip(pagos, pagos[1:]):
            if a["valor"] == b["valor"] and (date.fromisoformat(b["data"]) - date.fromisoformat(a["data"])).days <= DIAS_DUPLICADO:
                achados.append({"nome": c["nome"], "valor": a["valor"], "datas": [a["data"], b["data"]]})
    return achados


def frases(situacoes: list, dobrados: list, moeda="R$") -> list:
    def br(d):
        return f"{d[8:10]}/{d[5:7]}"
    linhas = []
    for s in situacoes:
        if s["situacao"] == "vencida":
            linhas.append(f"{s['nome']} venceu em {br(s['vencimento'])} e não achei o pagamento")
        elif s["situacao"] == "a_vencer":
            linhas.append(f"{s['nome']} vence em {br(s['vencimento'])}")
    for d in dobrados:
        linhas.append(f"{d['nome']} paga duas vezes ({moeda} {d['valor'].replace('.', ',')} em {br(d['datas'][0])} e {br(d['datas'][1])})")
    return linhas
