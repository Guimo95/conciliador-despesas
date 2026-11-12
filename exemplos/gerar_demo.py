"""Gera exemplos/demo_belvo.json: seis meses de despesas fictícias (Ana e Bruno), para ver o painel com histórico.

    python exemplos/gerar_demo.py
    python -m despesas --pasta demo importar exemplos/demo_belvo.json
"""
import json
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
FIXAS = [("ALUGUEL APTO", 2200, 5), ("ENERGIA ELETRICA SA", 190, 12), ("INTERNET FIBRA", 120, 15), ("STREAMING FILMES", 40, 20)]
VARIAVEIS = [("SUPERMERCADO BOM PRECO", 90, 420, 6), ("PADARIA DO CENTRO", 12, 45, 8), ("POSTO CAMINHO", 120, 260, 3),
             ("FARMACIA CENTRAL", 25, 140, 2), ("PET SHOP AMIGO", 60, 180, 1), ("RESTAURANTE SABOR", 40, 160, 3)]


def main():
    hoje = date(2026, 11, 12)
    linhas = []
    inicio = date(2026, 5, 1)
    mes = inicio
    while mes <= hoje:
        for nome, valor, dia in FIXAS:
            d = mes.replace(day=dia)
            if d <= hoje:
                linhas.append((d, nome, valor))
        for nome, minimo, maximo, vezes in VARIAVEIS:
            for _ in range(vezes):
                d = mes + timedelta(days=random.randint(0, 27))
                if d <= hoje:
                    linhas.append((d, nome, round(random.uniform(minimo, maximo), 2)))
        mes = (mes.replace(day=28) + timedelta(days=4)).replace(day=1)
    dados = [{"value_date": d.isoformat(), "description": n, "amount": v, "local_currency_amount": v, "type": "OUTFLOW",
              "account": {"name": "Cartão"}} for d, n, v in sorted(linhas)]
    destino = Path(__file__).with_name("demo_belvo.json")
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(dados)} transações fictícias em {destino}")


if __name__ == "__main__":
    main()
