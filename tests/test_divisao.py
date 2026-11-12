from decimal import Decimal

import pytest

from despesas.config import Config, Divisao, ErroConfig, carregar_config
from despesas.divisao import acerto, dividir, fracoes_do_lancamento, frase_acerto

D = Decimal


def cfg(modo="por_categoria", pessoas=("Ana", "Bruno"), **kw):
    return Config(titular="Ana", pessoas=list(pessoas), divisao=Divisao(modo=modo, padrao={"Ana": D(1)}, **kw))


def test_individual_tudo_do_titular():
    c = cfg("individual", pessoas=("Ana",))
    assert dividir(100, fracoes_do_lancamento(c, "Casa"), "Ana") == {"Ana": D("100.00")}


def test_por_categoria_e_padrao():
    c = cfg(categorias={"Casa": {"Ana": D("0.5"), "Bruno": D("0.5")}, "Mercado": {"Ana": D("0.7"), "Bruno": D("0.3")}})
    assert dividir("50.79", fracoes_do_lancamento(c, "Mercado"), "Ana") == {"Ana": D("35.55"), "Bruno": D("15.24")}
    assert dividir(80, fracoes_do_lancamento(c, "Lazer"), "Ana") == {"Ana": D("80.00")}


def test_arredondamento_soma_o_valor_e_sobra_fica_com_o_titular():
    partes = dividir("100.00", {"Ana": D(1) / 3, "Bruno": D(1) / 3, "Caio": D(1) / 3}, "Ana")
    assert sum(partes.values()) == D("100.00") and partes["Ana"] == D("33.34")


def test_modo_igual_com_categoria_sem_divisao():
    c = cfg("igual", pessoas=("Ana", "Bruno", "Caio"), sem_divisao=["Saúde"])
    assert dividir(90, fracoes_do_lancamento(c, "Casa"), "Ana") == {"Ana": D("30.00"), "Bruno": D("30.00"), "Caio": D("30.00")}
    assert dividir(90, fracoes_do_lancamento(c, "Saúde"), "Ana") == {"Ana": D("90.00")}


def test_excecao_por_estabelecimento_e_divisao_manual():
    c = cfg(categorias={"Mercado": {"Ana": D("0.7"), "Bruno": D("0.3")}},
            excecoes=[{"padrao": "PADARIA", "divisao": {"Ana": D("0.5"), "Bruno": D("0.5")}}])
    assert fracoes_do_lancamento(c, "Mercado", "PADARIA DO CENTRO") == {"Ana": D("0.5"), "Bruno": D("0.5")}
    assert fracoes_do_lancamento(c, "Mercado", "X", "Ana=0.2;Bruno=0.8") == {"Ana": D("0.2"), "Bruno": D("0.8")}
    with pytest.raises(ErroConfig):
        fracoes_do_lancamento(c, "Mercado", "X", "Ana=0.2;Bruno=0.7")


def test_acerto_com_pagamento_entre_pessoas():
    c = cfg()
    lanc = [{"valor": D(100), "pago_por": "Ana", "partes": {"Ana": D(50), "Bruno": D(50)}},
            {"valor": D(30), "pago_por": "Bruno", "partes": {"Ana": D(15), "Bruno": D(15)}}]
    saldos = acerto(lanc, c)
    assert saldos == {"Ana": D("35.00"), "Bruno": D("-35.00")}
    assert frase_acerto(saldos) == ["Bruno deve R$ 35,00 a Ana"]
    pago = acerto(lanc, c, [{"de": "Bruno", "para": "Ana", "valor": "35"}])
    assert frase_acerto(pago) == ["Ninguém deve nada"]


def test_config_valida_fracoes(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text("titular: Ana\npessoas: [Ana, Bruno]\ndivisao:\n  modo: por_categoria\n  categorias:\n    Casa: {Ana: 0.5, Bruno: 0.4}\n", encoding="utf-8")
    with pytest.raises(ErroConfig, match="somam"):
        carregar_config(p)
    p.write_text("titular: Ana\n", encoding="utf-8")
    assert carregar_config(p).divisao.modo == "individual"
