from datetime import date

from despesas.alertas import duplicados, frases, verificar
from despesas.relatorio import texto

CONTAS = [{"nome": "Aluguel", "padrao": "ALUGUEL", "dia": 5, "valor": 2200, "aviso_dias": 3},
          {"nome": "Luz", "padrao": "ENERGIA", "dia": 12, "aviso_dias": 3},
          {"nome": "Internet", "padrao": "INTERNET", "dia": 15, "valor": 120, "aviso_dias": 2}]


def l(data, desc, valor):
    return {"data": data, "descricao_banco": desc, "valor": valor, "tipo": "saida", "status": "classificado"}


def test_paga_vencida_a_vencer_e_ok():
    livro = [l("2026-11-04", "ALUGUEL APTO", "2200.00"), l("2026-10-12", "ENERGIA SA", "180.00")]
    s = {x["nome"]: x["situacao"] for x in verificar(CONTAS, livro, date(2026, 11, 13))}
    assert s == {"Aluguel": "paga", "Luz": "vencida", "Internet": "a_vencer"}
    s = {x["nome"]: x["situacao"] for x in verificar(CONTAS, livro, date(2026, 11, 8))}
    assert s["Internet"] == "ok" and s["Luz"] == "ok"


def test_valor_fora_da_tolerancia_nao_conta_como_pago():
    livro = [l("2026-11-04", "ALUGUEL APTO", "300.00")]  # outra coisa com "aluguel" no nome
    assert verificar(CONTAS, livro, date(2026, 11, 6))[0]["situacao"] == "vencida"


def test_pagamento_em_dobro_e_frases():
    livro = [l("2026-11-10", "ENERGIA SA", "83.08"), l("2026-11-14", "ENERGIA SA", "83.08")]
    dobro = duplicados(CONTAS, livro, date(2026, 11, 15))
    assert dobro == [{"nome": "Luz", "valor": "83.08", "datas": ["2026-11-10", "2026-11-14"]}]
    assert "Luz paga duas vezes (R$ 83,08 em 10/11 e 14/11)" in frases([], dobro)


def test_texto_do_report():
    from decimal import Decimal
    r = {"mes": "2026-11", "total": Decimal("1234.5"), "categorias": [("Casa", Decimal("1000"))],
         "pessoas": [("Ana", Decimal("800")), ("Bruno", Decimal("434.5"))], "acerto": ["Bruno deve R$ 434,50 a Ana"],
         "alertas": ["Luz vence em 12/11"],
         "perguntas": [{"data": "2026-11-06", "descricao_banco": "LOJA X", "valor": "87.40", "motivo": "O que foi?"},
                       {"data": "2026-11-02", "descricao_banco": "BAR Y", "valor": "40.00", "motivo": "Sem regra"},
                       {"data": "2026-11-09", "descricao_banco": "BAR Y", "valor": "60.00", "motivo": "Sem regra"}]}
    t = texto(r)
    assert "Despesas de 11/2026 até agora: R$ 1.234,50" in t and "Parte de Bruno: R$ 434,50" in t
    assert "1. BAR Y: 2 lançamentos de 02/11 a 09/11, R$ 100,00 no total: Sem regra" in t  # agrupado
    assert "2. 06/11 LOJA X R$ 87,40: O que foi?" in t and "- Luz vence em 12/11" in t
