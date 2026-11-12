"""Fluxo completo com os exemplos fictícios: importar OFX, CSV de fatura e Belvo, sem duplicar, e conferir as somas."""
import shutil
from decimal import Decimal
from pathlib import Path

import pytest

from despesas import livro as L
from despesas.__main__ import main
from despesas.importar import ler_belvo, ler_ofx
from despesas.regras import classificar

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture
def pasta(tmp_path):
    destino = tmp_path / "meus-dados"
    shutil.copytree(RAIZ / "config" / "exemplo", destino)
    return destino


def rodar(pasta, *args):
    main(["--pasta", str(pasta), *args])


def test_ofx_le_sgml_com_virgula_e_sinal():
    linhas = ler_ofx(RAIZ / "exemplos" / "extrato_exemplo.ofx")
    assert len(linhas) == 7
    assert linhas[1] == {"data": "2026-11-03", "descricao_banco": "SUPERMERCADO BOM PRECO", "valor": "412.35",
                         "tipo": "saida", "origem": "ofx", "conta": "", "parcela": ""}
    assert linhas[3]["tipo"] == "entrada"


def test_belvo_usa_valor_em_reais():
    linhas = ler_belvo(RAIZ / "exemplos" / "belvo_exemplo.json")
    assert linhas[1]["valor"] == "54.32" and linhas[2]["tipo"] == "entrada"


def test_ordem_das_regras_ignorar_antes_de_categoria():
    regras = {"ignorar": ["FATURA"], "perguntar": [], "regras": [{"padrao": "CARTAO|FATURA", "categoria": "Casa"}]}
    assert classificar("PAGAMENTO DE FATURA CARTAO", regras).acao == "ignorar"
    assert classificar("x", regras, respostas={"X": {"categoria": "Lazer"}}).categoria == "Lazer"


def test_fluxo_completo(pasta, capsys):
    rodar(pasta, "importar", str(RAIZ / "exemplos" / "extrato_exemplo.ofx"), "--conta", "Conta")
    rodar(pasta, "importar", str(RAIZ / "exemplos" / "fatura_exemplo.csv"), "--perfil", "fatura_exemplo", "--conta", "Cartão")
    rodar(pasta, "importar", str(RAIZ / "exemplos" / "belvo_exemplo.json"))
    rodar(pasta, "importar", str(RAIZ / "exemplos" / "extrato_exemplo.ofx"), "--conta", "Conta")  # de novo: nada entra
    saida = capsys.readouterr().out
    assert "0 lançamentos novos (7 já existiam)" in saida

    livro = L.ler(pasta / "livro.csv")
    assert len(livro) == 15
    por_status = {s: sum(l["status"] == s for l in livro) for s in ("classificado", "ignorado", "perguntar")}
    assert por_status == {"classificado": 11, "ignorado": 1, "perguntar": 3}  # loja online, restaurante, móveis

    divisoes = L.ler(pasta / "divisoes.csv")
    total = sum(Decimal(d["valor"]) for d in divisoes)
    # despesas classificadas: 189.90 + 412.35 + 33.33 + 250.10 + 39.90 + 72.15 + 120 + 150 + 54.32 - 20 (estorno) = 1302.05
    assert total == Decimal("1302.05")
    bruno = sum(Decimal(d["valor"]) for d in divisoes if d["pessoa"] == "Bruno")
    # Casa 189.90 * 0.5 + Mercado (412.35 + 250.10 - 20) * 0.3 + padaria 33.33 * 0.5 + Pets 120 * 0.5
    # arredondamento bancário: 123,705 -> 123,70 e 16,665 -> 16,66
    assert bruno == Decimal("94.95") + Decimal("123.70") + Decimal("75.03") - Decimal("6.00") + Decimal("16.66") + Decimal("60.00")

    # resposta da pessoa vira regra e o reaplicar tira da lista de perguntas
    (pasta / "respostas.yaml").write_text("RESTAURANTE SABOR: {categoria: Lazer, descricao: Jantar}\n", encoding="utf-8")
    rodar(pasta, "reaplicar")
    assert "1 lançamentos reclassificados; 2 ainda com pergunta" in capsys.readouterr().out

    rodar(pasta, "acerto")
    assert "Bruno deve R$" in capsys.readouterr().out
