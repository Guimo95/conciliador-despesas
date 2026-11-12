"""Saídas para a pessoa ver: painel HTML (arquivo único, abre no navegador sem internet) e planilha Excel."""
import json
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from . import livro as L
from .config import Config
from .divisao import acerto, frase_acerto
from .notas import ler_notas, ligar

RAIZ = Path(__file__).resolve().parent.parent
MODELO_PAINEL = RAIZ / "painel" / "painel.html"
ECHARTS = RAIZ / "painel" / "vendor" / "echarts-5.5.1.min.js"


def montar_dados(pasta: Path, cfg: Config, receitas=("Receita",), hoje: date | None = None, tema="neutro") -> dict:
    """Dados do painel: só despesas classificadas (estorno negativo) com a parte de cada pessoa, e as pendências."""
    livro = L.ler(pasta / "livro.csv")
    partes = defaultdict(dict)
    for d in L.ler(pasta / "divisoes.csv"):
        partes[d["id"]][d["pessoa"]] = float(d["valor"])
    lancamentos, pendencias = [], []
    for l in livro:
        if l["status"] == "perguntar":
            pendencias.append({"data": l["data"], "descricao": l["descricao_banco"], "valor": float(l["valor"]), "motivo": l["motivo"]})
        if l["status"] != "classificado" or l["categoria"] in receitas:
            continue
        sinal = 1 if l.get("tipo", "saida") == "saida" else -1
        lancamentos.append({"id": l["id"], "data": l["data"], "categoria": l["categoria"],
                            "descricao": l["descricao"] or l["descricao_banco"], "conta": l.get("conta", ""),
                            "valor": round(sinal * float(l["valor"]), 2), "partes": partes.get(l["id"], {})})
    ultima = max((l["data"] for l in livro), default="")
    notas, itens = ler_notas(pasta)
    ligacoes = ligar(notas, livro)
    lista_itens = [{"id_lancamento": ligacoes.get(i["nota"], ""), "nota": i["nota"], "descricao": i["descricao"],
                    "quantidade": float(i["quantidade"] or 0), "unidade": i.get("unidade", ""),
                    "valor_unitario": float(i["valor_unitario"] or 0), "valor_total": float(i["valor_total"] or 0),
                    "tipo": i["tipo"]} for i in itens]
    return {"titular": cfg.titular, "pessoas": cfg.pessoas, "moeda": cfg.moeda, "tema": tema,
            "hoje": (hoje or date.today()).isoformat(), "dados_ate": ultima,
            "lancamentos": lancamentos, "pendencias": pendencias, "itens": lista_itens,
            "notas_ligadas": len(ligacoes), "notas_total": len(notas)}


def gerar_painel(dados: dict, saida: Path) -> Path:
    html = MODELO_PAINEL.read_text(encoding="utf-8")
    # "</" escapado para o JSON não fechar a tag <script> se alguma descrição tiver "</script>"
    bruto = json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("/*__DADOS__*/null", bruto).replace("/*__ECHARTS__*/", ECHARTS.read_text(encoding="utf-8"))
    saida.write_text(html, encoding="utf-8")
    return saida


def gerar_planilha(pasta: Path, cfg: Config, saida: Path, receitas=("Receita",)) -> Path:
    """Planilha com valores prontos (sem fórmulas): resumo por mês e categoria, parte de cada pessoa,
    lançamentos, pendências e acerto."""
    livro = {l["id"]: l for l in L.ler(pasta / "livro.csv")}
    divisoes = L.ler(pasta / "divisoes.csv")
    por_cat = defaultdict(lambda: defaultdict(Decimal))
    por_pessoa = defaultdict(lambda: defaultdict(Decimal))
    partes_por_id = defaultdict(dict)
    for d in divisoes:
        l = livro[d["id"]]
        mes = l["data"][:7]
        valor = Decimal(d["valor"])
        por_cat[l["categoria"]][mes] += valor
        por_pessoa[d["pessoa"]][mes] += valor
        partes_por_id[d["id"]][d["pessoa"]] = valor
    meses = sorted({l["data"][:7] for l in livro.values()})

    wb = Workbook()
    titulo, cabec = Font(bold=True, size=13), Font(bold=True, color="FFFFFF")
    fundo = PatternFill("solid", fgColor="1F3A4D")
    moeda = '"R$" #,##0.00'

    def cabecalho(ws, linha, textos):
        for i, t in enumerate(textos, start=1):
            c = ws.cell(linha, i, t)
            c.font, c.fill, c.alignment = cabec, fundo, Alignment(horizontal="center")

    ws = wb.active
    ws.title = "Resumo"
    ws["A1"], ws["A1"].font = f"Despesas por categoria e mês (dados até {max(meses, default='')})", titulo
    cabecalho(ws, 3, ["Categoria"] + meses + ["Total"])
    for i, (cat, valores) in enumerate(sorted(por_cat.items(), key=lambda x: -sum(x[1].values())), start=4):
        ws.cell(i, 1, cat)
        for j, mes in enumerate(meses, start=2):
            ws.cell(i, j, float(valores.get(mes, 0))).number_format = moeda
        ws.cell(i, len(meses) + 2, float(sum(valores.values()))).number_format = moeda
    ws.column_dimensions["A"].width = 26

    if len(cfg.pessoas) > 1:
        ws = wb.create_sheet("Pessoas")
        cabecalho(ws, 1, ["Pessoa"] + meses + ["Total"])
        for i, p in enumerate(cfg.pessoas, start=2):
            ws.cell(i, 1, p)
            for j, mes in enumerate(meses, start=2):
                ws.cell(i, j, float(por_pessoa[p].get(mes, 0))).number_format = moeda
            ws.cell(i, len(meses) + 2, float(sum(por_pessoa[p].values()))).number_format = moeda
        lanc = []
        for id_, partes in partes_por_id.items():
            l = livro[id_]
            sinal = Decimal(1) if l.get("tipo", "saida") == "saida" else Decimal(-1)
            lanc.append({"valor": Decimal(l["valor"]) * sinal, "pago_por": l.get("pago_por"), "partes": partes})
        frases = frase_acerto(acerto(lanc, cfg, L.ler(pasta / "pagamentos.csv")), cfg.moeda)
        ws.cell(len(cfg.pessoas) + 3, 1, "Acerto").font = titulo
        for k, frase in enumerate(frases):
            ws.cell(len(cfg.pessoas) + 4 + k, 1, frase)
        ws.column_dimensions["A"].width = 40

    ws = wb.create_sheet("Lançamentos")
    colunas = ["data", "conta", "descricao_banco", "categoria", "descricao", "valor", "status"] + [f"parte {p}" for p in cfg.pessoas]
    cabecalho(ws, 1, colunas)
    for i, l in enumerate(sorted(livro.values(), key=lambda x: x["data"], reverse=True), start=2):
        for j, c in enumerate(colunas[:7], start=1):
            ws.cell(i, j, float(l[c]) if c == "valor" else l[c])
        ws.cell(i, 6).number_format = moeda
        for j, p in enumerate(cfg.pessoas, start=8):
            v = partes_por_id.get(l["id"], {}).get(p)
            if v is not None:
                ws.cell(i, j, float(v)).number_format = moeda
    ws.freeze_panes = "A2"

    ws = wb.create_sheet("Pendências")
    cabecalho(ws, 1, ["data", "descricao_banco", "valor", "motivo"])
    for i, l in enumerate([l for l in livro.values() if l["status"] == "perguntar"], start=2):
        ws.cell(i, 1, l["data"]); ws.cell(i, 2, l["descricao_banco"])
        ws.cell(i, 3, float(l["valor"])).number_format = moeda; ws.cell(i, 4, l["motivo"])

    temporario = saida.with_suffix(".tmp.xlsx")
    wb.save(temporario)
    temporario.replace(saida)  # se a planilha estiver aberta no Excel, o replace falha e a antiga continua inteira
    return saida
