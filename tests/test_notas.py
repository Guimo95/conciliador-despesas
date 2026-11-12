"""Notas de compra: tipo do item pelo yaml, ligação com o lançamento e itens no painel."""
import json
import re
import shutil
from pathlib import Path

from despesas.__main__ import main
from despesas.notas import ligar, tipo_do_item

RAIZ = Path(__file__).resolve().parent.parent


def test_tipo_do_item_e_ligacao():
    tipos = [{"tipo": "Laticínios", "padroes": ["LEITE"]}, {"tipo": "Feira", "padroes": ["BANANA"]}]
    assert tipo_do_item("LEITE INTEGRAL 1L", tipos) == "Laticínios" and tipo_do_item("X", tipos) == ""
    livro = [{"id": "a", "data": "2026-11-05", "valor": "50.00", "tipo": "saida", "status": "classificado"},
             {"id": "b", "data": "2026-11-20", "valor": "50.00", "tipo": "saida", "status": "classificado"}]
    notas = [{"nota": "N1", "data": "2026-11-03", "valor_pago": "50.00"},   # até 5 dias depois: liga com "a"
             {"nota": "N2", "data": "2026-11-10", "valor_pago": "50.00"}]   # "b" está 10 dias depois: não liga
    assert ligar(notas, livro) == {"N1": "a"}


def test_painel_traz_itens_ligados(tmp_path):
    pasta = tmp_path / "meus-dados"
    shutil.copytree(RAIZ / "config" / "exemplo", pasta)
    shutil.copy(RAIZ / "exemplos" / "notas.csv", pasta / "notas.csv")
    shutil.copy(RAIZ / "exemplos" / "itens.csv", pasta / "itens.csv")
    main(["--pasta", str(pasta), "importar", str(RAIZ / "exemplos" / "extrato_exemplo.ofx")])
    main(["--pasta", str(pasta), "importar", str(RAIZ / "exemplos" / "fatura_exemplo.csv"), "--perfil", "fatura_exemplo"])
    main(["--pasta", str(pasta), "painel", "--hoje", "2026-11-12"])
    html = (pasta / "painel.html").read_text(encoding="utf-8")
    dados = json.loads(re.search(r"const D = (\{.*?\});\n", html, re.S).group(1))
    assert dados["notas_ligadas"] == 2 and len(dados["itens"]) == 21
    tipos = {i["descricao"]: i["tipo"] for i in dados["itens"]}
    assert tipos["LEITE INTEGRAL 1L"] == "Laticínios" and tipos["CERVEJA LATA"] == "Bebidas"  # tipo já preenchido é mantido
    assert all(i["id_lancamento"] for i in dados["itens"])
