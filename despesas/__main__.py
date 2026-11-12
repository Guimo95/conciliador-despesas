"""Linha de comando. Tudo fica numa pasta de dados da pessoa (padrão: ./meus-dados), fora do repositório.

    python -m despesas importar extrato.ofx --conta "Conta corrente"
    python -m despesas importar fatura.csv --perfil fatura_banco_x --conta "Cartão"
    python -m despesas importar belvo.json --tipo belvo
    python -m despesas reaplicar            (depois de responder dúvidas ou criar regra)
    python -m despesas resumo --mes 2026-11
    python -m despesas acerto
    python -m despesas painel               (gera meus-dados/painel.html)
    python -m despesas planilha             (gera meus-dados/despesas.xlsx)
    python -m despesas alertas              (contas vencidas, a vencer e pagas em dobro)
    python -m despesas report               (rascunho do report com os números do mês)
"""
import argparse
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import yaml

from . import livro as L
from .config import ErroConfig, carregar_config, carregar_regras
from .divisao import acerto, frase_acerto
from .importar import ler_belvo, ler_csv_banco, ler_ofx
from .processar import calcular_divisoes, classificar_novos, reaplicar


def _yaml(caminho):
    p = Path(caminho)
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.exists() else {}


def _contexto(pasta: Path):
    cfg = carregar_config(pasta / "config.yaml")
    regras = carregar_regras(pasta / "regras.yaml")
    respostas = _yaml(pasta / "respostas.yaml")
    receitas = tuple(_yaml(pasta / "config.yaml").get("categorias_receita", ["Receita"]))
    return cfg, regras, respostas, receitas


def _salvar(pasta, livro, cfg, receitas):
    L.gravar(pasta / "livro.csv", livro)
    L.gravar(pasta / "divisoes.csv", calcular_divisoes(livro, cfg, receitas), L.COLUNAS_DIVISAO)


def cmd_importar(args, pasta):
    cfg, regras, respostas, receitas = _contexto(pasta)
    tipo = args.tipo or ("ofx" if args.arquivo.lower().endswith(".ofx") else "belvo" if args.arquivo.lower().endswith(".json") else "csv")
    if tipo == "ofx":
        novos = ler_ofx(args.arquivo, args.conta)
    elif tipo == "belvo":
        novos = ler_belvo(args.arquivo, args.conta)
    else:
        perfis = _yaml(pasta / "config.yaml").get("perfis_csv", {})
        if args.perfil not in perfis:
            sys.exit(f"Informe --perfil com um dos perfis do config.yaml: {list(perfis)}")
        novos = ler_csv_banco(args.arquivo, perfis[args.perfil], args.conta)
    classificar_novos(novos, regras, cfg, respostas)
    livro, entraram = L.acrescentar(L.ler(pasta / "livro.csv"), novos)
    _salvar(pasta, livro, cfg, receitas)
    perguntas = [l for l in entraram if l["status"] == "perguntar"]
    print(f"{len(entraram)} lançamentos novos ({len(novos) - len(entraram)} já existiam) | "
          f"{sum(l['status'] == 'classificado' for l in entraram)} classificados | "
          f"{sum(l['status'] == 'ignorado' for l in entraram)} ignorados | {len(perguntas)} com pergunta")
    for p in perguntas:
        print(f"  ? {p['data']} {p['descricao_banco']} {cfg.moeda} {p['valor']}: {p['motivo']}")


def cmd_reaplicar(args, pasta):
    cfg, regras, respostas, receitas = _contexto(pasta)
    livro = L.ler(pasta / "livro.csv")
    mudou = reaplicar(livro, regras, respostas)
    _salvar(pasta, livro, cfg, receitas)
    print(f"{mudou} lançamentos reclassificados; {sum(l['status'] == 'perguntar' for l in livro)} ainda com pergunta")


def _no_mes(l, mes):
    return not mes or l["data"].startswith(mes)


def cmd_resumo(args, pasta):
    cfg, _, _, receitas = _contexto(pasta)
    livro = {l["id"]: l for l in L.ler(pasta / "livro.csv")}
    por_categoria = defaultdict(Decimal)
    por_pessoa = defaultdict(Decimal)
    for d in L.ler(pasta / "divisoes.csv"):
        l = livro.get(d["id"])
        if l and _no_mes(l, args.mes):
            por_categoria[l["categoria"]] += Decimal(d["valor"])
            por_pessoa[d["pessoa"]] += Decimal(d["valor"])
    total = sum(por_categoria.values())
    print(f"Despesas {args.mes or 'de todo o período'}: {cfg.moeda} {total:.2f}")
    for cat, v in sorted(por_categoria.items(), key=lambda x: -x[1]):
        print(f"  {cat:<28} {cfg.moeda} {v:>10.2f}")
    if len(cfg.pessoas) > 1:
        print("Parte de cada pessoa:")
        for p in cfg.pessoas:
            print(f"  {p:<28} {cfg.moeda} {por_pessoa[p]:>10.2f}")
    pend = sum(1 for l in livro.values() if l["status"] == "perguntar" and _no_mes(l, args.mes))
    print(f"Pendências: {pend}")


def cmd_acerto(args, pasta):
    cfg, _, _, receitas = _contexto(pasta)
    livro = {l["id"]: l for l in L.ler(pasta / "livro.csv")}
    partes = defaultdict(dict)
    for d in L.ler(pasta / "divisoes.csv"):
        partes[d["id"]][d["pessoa"]] = Decimal(d["valor"])
    lanc = []
    for id_, p in partes.items():
        l = livro[id_]
        sinal = Decimal(1) if l.get("tipo", "saida") == "saida" else Decimal(-1)
        lanc.append({"valor": Decimal(l["valor"]) * sinal, "pago_por": l.get("pago_por"), "partes": p})
    pagamentos = L.ler(pasta / "pagamentos.csv")  # data;de;para;valor
    for frase in frase_acerto(acerto(lanc, cfg, pagamentos), cfg.moeda):
        print(frase)


def cmd_painel(args, pasta):
    from datetime import date

    from .saidas import gerar_painel, montar_dados
    cfg, _, _, receitas = _contexto(pasta)
    tema = _yaml(pasta / "config.yaml").get("tema", "neutro")
    hoje = date.fromisoformat(args.hoje) if args.hoje else None
    saida = gerar_painel(montar_dados(pasta, cfg, receitas, hoje, tema), pasta / "painel.html")
    print(f"Painel gerado: {saida.resolve()} (abra no navegador)")


def _hoje(args):
    from datetime import date
    return date.fromisoformat(args.hoje) if getattr(args, "hoje", "") else date.today()


def cmd_alertas(args, pasta):
    from .alertas import carregar_contas, duplicados, frases, verificar
    cfg = carregar_config(pasta / "config.yaml")
    contas = carregar_contas(pasta / "contas.yaml")
    if not contas:
        sys.exit("Sem contas.yaml: nada a verificar.")
    livro = L.ler(pasta / "livro.csv")
    linhas = frases(verificar(contas, livro, _hoje(args)), duplicados(contas, livro, _hoje(args)), cfg.moeda)
    print("\n".join(linhas) if linhas else "Nenhum alerta de conta.")


def cmd_report(args, pasta):
    from .relatorio import montar, texto
    cfg = carregar_config(pasta / "config.yaml")
    print(texto(montar(pasta, cfg, _hoje(args), args.mes), cfg.moeda))


def cmd_planilha(args, pasta):
    from .saidas import gerar_planilha
    cfg, _, _, receitas = _contexto(pasta)
    try:
        saida = gerar_planilha(pasta, cfg, pasta / "despesas.xlsx", receitas)
    except PermissionError:
        sys.exit("A planilha está aberta no Excel. Feche e rode de novo.")
    print(f"Planilha gerada: {saida.resolve()}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="despesas", description="Conciliador de despesas")
    ap.add_argument("--pasta", default="meus-dados", help="pasta com config.yaml, regras.yaml e o livro (padrão: meus-dados)")
    sub = ap.add_subparsers(dest="comando", required=True)
    p = sub.add_parser("importar")
    p.add_argument("arquivo")
    p.add_argument("--tipo", choices=["ofx", "csv", "belvo"])
    p.add_argument("--perfil", default="")
    p.add_argument("--conta", default="")
    sub.add_parser("reaplicar")
    p = sub.add_parser("resumo")
    p.add_argument("--mes", default="")
    sub.add_parser("acerto")
    p = sub.add_parser("painel")
    p.add_argument("--hoje", default="", help="data de referência AAAA-MM-DD (padrão: hoje)")
    sub.add_parser("planilha")
    p = sub.add_parser("alertas")
    p.add_argument("--hoje", default="")
    p = sub.add_parser("report")
    p.add_argument("--hoje", default="")
    p.add_argument("--mes", default="")
    args = ap.parse_args(argv)
    pasta = Path(args.pasta)
    comandos = {"importar": cmd_importar, "reaplicar": cmd_reaplicar, "resumo": cmd_resumo, "acerto": cmd_acerto,
                "painel": cmd_painel, "planilha": cmd_planilha, "alertas": cmd_alertas, "report": cmd_report}
    try:
        comandos[args.comando](args, pasta)
    except (ErroConfig, FileNotFoundError, KeyError) as erro:
        sys.exit(f"Erro: {erro}")


if __name__ == "__main__":
    main()
