"""Notas de compra (opcional): itens de cupom fiscal (NFC-e) ligados ao lançamento do banco.

O agente grava, a partir da foto ou do QR code do cupom:
  meus-dados/notas.csv  -> nota;data;loja;valor_pago;desconto
  meus-dados/itens.csv  -> nota;descricao;quantidade;unidade;valor_unitario;valor_total;tipo
Os itens detalham a despesa; não somam de novo no total.
"""
import re
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import yaml

from . import livro as L

COLUNAS_NOTAS = ["nota", "data", "loja", "valor_pago", "desconto"]
COLUNAS_ITENS = ["nota", "descricao", "quantidade", "unidade", "valor_unitario", "valor_total", "tipo"]


def carregar_tipos(caminho) -> list:
    """tipos_produto.yaml: lista de {tipo, padroes: [...]}. Primeiro padrão que casar vence."""
    p = Path(caminho)
    if not p.exists():
        return []
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("tipos", [])


def tipo_do_item(descricao: str, tipos: list) -> str:
    for t in tipos:
        if any(re.search(p, descricao, flags=re.IGNORECASE) for p in t.get("padroes", [])):
            return t["tipo"]
    return ""


def ligar(notas: list, livro: list, dias=5) -> dict:
    """nota -> id do lançamento: mesmo valor pago, do dia da nota até N dias depois (a compra no cartão
    pode aparecer com atraso). Cada lançamento recebe no máximo uma nota."""
    usados, ligacoes = set(), {}
    candidatos = [l for l in livro if l.get("tipo", "saida") == "saida" and l.get("status") != "ignorado"]
    for n in sorted(notas, key=lambda x: x["data"]):
        dia = date.fromisoformat(n["data"])
        valor = Decimal(n["valor_pago"])
        for l in sorted(candidatos, key=lambda x: x["data"]):
            d = date.fromisoformat(l["data"])
            if l["id"] not in usados and Decimal(l["valor"]) == valor and dia <= d <= dia + timedelta(days=dias):
                ligacoes[n["nota"]] = l["id"]
                usados.add(l["id"])
                break
    return ligacoes


def ler_notas(pasta: Path):
    notas = L.ler(pasta / "notas.csv")
    itens = L.ler(pasta / "itens.csv")
    tipos = carregar_tipos(pasta / "tipos_produto.yaml")
    for i in itens:
        if not i.get("tipo"):
            i["tipo"] = tipo_do_item(i["descricao"], tipos) or "Sem tipo"
    return notas, itens
