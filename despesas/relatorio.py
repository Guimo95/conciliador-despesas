"""Números do report: o agente escreve a mensagem a partir daqui, sem fazer conta."""
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from . import livro as L
from .alertas import carregar_contas, duplicados, frases, verificar
from .config import Config
from .divisao import acerto, frase_acerto


def _br(valor, moeda):
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{moeda} {texto}"


def montar(pasta: Path, cfg: Config, hoje: date, mes: str = "") -> dict:
    mes = mes or hoje.strftime("%Y-%m")
    livro = L.ler(pasta / "livro.csv")
    por_id = {l["id"]: l for l in livro}
    por_cat, por_pessoa = defaultdict(Decimal), defaultdict(Decimal)
    partes = defaultdict(dict)
    for d in L.ler(pasta / "divisoes.csv"):
        l = por_id[d["id"]]
        partes[d["id"]][d["pessoa"]] = Decimal(d["valor"])
        if l["data"].startswith(mes):
            por_cat[l["categoria"]] += Decimal(d["valor"])
            por_pessoa[d["pessoa"]] += Decimal(d["valor"])
    lanc = []
    for id_, p in partes.items():
        l = por_id[id_]
        sinal = Decimal(1) if l.get("tipo", "saida") == "saida" else Decimal(-1)
        lanc.append({"valor": Decimal(l["valor"]) * sinal, "pago_por": l.get("pago_por"), "partes": p})
    contas = carregar_contas(pasta / "contas.yaml")
    return {
        "mes": mes,
        "total": sum(por_cat.values()),
        "categorias": sorted(por_cat.items(), key=lambda x: -x[1]),
        "pessoas": [(p, por_pessoa[p]) for p in cfg.pessoas] if len(cfg.pessoas) > 1 else [],
        "acerto": frase_acerto(acerto(lanc, cfg, L.ler(pasta / "pagamentos.csv")), cfg.moeda) if len(cfg.pessoas) > 1 else [],
        "alertas": frases(verificar(contas, livro, hoje), duplicados(contas, livro, hoje), cfg.moeda),
        "perguntas": [l for l in livro if l["status"] == "perguntar"],
    }


def texto(r: dict, moeda="R$") -> str:
    """Rascunho em texto simples. O agente pode reescrever, mas os números são estes."""
    mes = r["mes"]
    linhas = [f"Despesas de {mes[5:7]}/{mes[:4]} até agora: {_br(r['total'], moeda)}"]
    if r["categorias"]:
        linhas.append("Maiores categorias: " + "; ".join(f"{c} {_br(v, moeda)}" for c, v in r["categorias"][:3]))
    for p, v in r["pessoas"]:
        linhas.append(f"Parte de {p}: {_br(v, moeda)}")
    if r["acerto"]:
        linhas.append("Acerto acumulado (já descontados os pagamentos registrados): " + "; ".join(r["acerto"]))
    if r["alertas"]:
        linhas.append("Contas:")
        linhas += [f"- {a}" for a in r["alertas"]]
    if r["perguntas"]:
        # O mesmo estabelecimento vira uma pergunta só: uma resposta resolve todos os lançamentos dele.
        grupos = {}
        for l in sorted(r["perguntas"], key=lambda x: x["data"]):
            grupos.setdefault(l["descricao_banco"].strip().upper(), []).append(l)
        linhas.append("Dúvidas:")
        for i, (desc, ls) in enumerate(grupos.items(), start=1):
            d0, total = ls[0]["data"], sum(Decimal(x["valor"]) for x in ls)
            if len(ls) == 1:
                quando = f"{d0[8:10]}/{d0[5:7]} {ls[0]['descricao_banco']} {_br(total, moeda)}"
            else:
                d1 = ls[-1]["data"]
                quando = (f"{ls[0]['descricao_banco']}: {len(ls)} lançamentos de {d0[8:10]}/{d0[5:7]} a "
                          f"{d1[8:10]}/{d1[5:7]}, {_br(total, moeda)} no total")
            linhas.append(f"{i}. {quando}: {ls[0]['motivo']}")
    return "\n".join(linhas)
