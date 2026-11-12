"""Painel HTML e planilha a partir dos exemplos fictícios."""
import json
import re
import shutil
from pathlib import Path

from openpyxl import load_workbook

from despesas.__main__ import main

RAIZ = Path(__file__).resolve().parent.parent


def preparar(tmp_path):
    pasta = tmp_path / "meus-dados"
    shutil.copytree(RAIZ / "config" / "exemplo", pasta)
    main(["--pasta", str(pasta), "importar", str(RAIZ / "exemplos" / "extrato_exemplo.ofx")])
    main(["--pasta", str(pasta), "importar", str(RAIZ / "exemplos" / "fatura_exemplo.csv"), "--perfil", "fatura_exemplo"])
    main(["--pasta", str(pasta), "importar", str(RAIZ / "exemplos" / "belvo_exemplo.json")])
    return pasta


def test_painel_embute_dados_e_biblioteca(tmp_path):
    pasta = preparar(tmp_path)
    main(["--pasta", str(pasta), "painel", "--hoje", "2026-11-12"])
    html = (pasta / "painel.html").read_text(encoding="utf-8")
    assert "/*__DADOS__*/" not in html and "/*__ECHARTS__*/" not in html
    assert "echarts" in html and "https://" not in html.split("<script>")[0]  # nada carregado de fora
    dados = json.loads(re.search(r"const D = (\{.*?\});\n", html, re.S).group(1))
    assert dados["pessoas"] == ["Ana", "Bruno"] and dados["hoje"] == "2026-11-12"
    assert round(sum(l["valor"] for l in dados["lancamentos"]), 2) == 1302.05  # mesmo total do teste de fluxo
    assert len(dados["pendencias"]) == 3


def test_planilha_tem_resumo_pessoas_e_acerto(tmp_path):
    pasta = preparar(tmp_path)
    main(["--pasta", str(pasta), "planilha"])
    wb = load_workbook(pasta / "despesas.xlsx")
    assert wb.sheetnames == ["Resumo", "Pessoas", "Lançamentos", "Pendências"]
    pessoas = wb["Pessoas"]
    total = sum(pessoas.cell(i, pessoas.max_column).value for i in (2, 3))
    assert round(total, 2) == 1302.05
    assert any("deve" in str(c.value) for c in pessoas["A"])
