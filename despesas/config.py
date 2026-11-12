"""Leitura e validação da configuração da pessoa (config.yaml, regras.yaml)."""
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import yaml

MODOS = ("individual", "por_categoria", "igual")


class ErroConfig(ValueError):
    pass


@dataclass
class Divisao:
    modo: str = "individual"
    padrao: dict = field(default_factory=dict)        # pessoa -> fração, para categoria sem regra
    categorias: dict = field(default_factory=dict)    # categoria -> {pessoa: fração}
    excecoes: list = field(default_factory=list)      # [{padrao: texto, divisao: {pessoa: fração}}]
    sem_divisao: list = field(default_factory=list)   # categorias que nunca dividem (modo igual)


@dataclass
class Config:
    titular: str
    pessoas: list
    divisao: Divisao
    moeda: str = "R$"


def _fracoes(origem, valores, pessoas):
    if not isinstance(valores, dict) or not valores:
        raise ErroConfig(f"{origem}: informe as frações por pessoa, ex.: {{Ana: 0.5, Bruno: 0.5}}")
    resultado = {}
    for pessoa, fracao in valores.items():
        if pessoa not in pessoas:
            raise ErroConfig(f"{origem}: '{pessoa}' não está na lista de pessoas {pessoas}")
        resultado[pessoa] = Decimal(str(fracao))
    if sum(resultado.values()) != Decimal(1):
        raise ErroConfig(f"{origem}: as frações somam {sum(resultado.values())}, mas precisam somar 1")
    return resultado


def carregar_config(caminho) -> Config:
    dados = yaml.safe_load(Path(caminho).read_text(encoding="utf-8")) or {}
    titular = dados.get("titular")
    if not titular:
        raise ErroConfig("config.yaml: informe o titular (quem é dono das contas)")
    pessoas = dados.get("pessoas") or [titular]
    if titular not in pessoas:
        pessoas = [titular] + list(pessoas)
    d = dados.get("divisao") or {}
    modo = d.get("modo", "individual" if len(pessoas) == 1 else "por_categoria")
    if modo not in MODOS:
        raise ErroConfig(f"config.yaml: modo de divisão '{modo}' inválido; use um de {MODOS}")
    divisao = Divisao(
        modo=modo,
        padrao=_fracoes("divisao.padrao", d.get("padrao") or {titular: 1}, pessoas),
        categorias={c: _fracoes(f"divisao.categorias.{c}", v, pessoas) for c, v in (d.get("categorias") or {}).items()},
        excecoes=[{"padrao": e["padrao"].upper(), "divisao": _fracoes(f"divisao.excecoes[{i}]", e["divisao"], pessoas)}
                  for i, e in enumerate(d.get("excecoes") or [])],
        sem_divisao=list(d.get("sem_divisao") or []),
    )
    return Config(titular=titular, pessoas=list(pessoas), divisao=divisao, moeda=dados.get("moeda", "R$"))


def carregar_regras(caminho) -> dict:
    dados = yaml.safe_load(Path(caminho).read_text(encoding="utf-8")) or {}
    for chave in ("ignorar", "perguntar", "regras"):
        dados.setdefault(chave, [])
    for i, r in enumerate(dados["regras"]):
        if not r.get("padrao") or not r.get("categoria"):
            raise ErroConfig(f"regras.yaml: a regra {i + 1} precisa de 'padrao' e 'categoria'")
    return dados
