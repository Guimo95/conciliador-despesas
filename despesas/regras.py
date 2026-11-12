"""Classificação de um lançamento pelas regras: ignorar, perguntar ou categoria. A primeira regra que casar vence."""
import re
from dataclasses import dataclass


@dataclass
class Classificacao:
    acao: str               # ignorar | perguntar | classificado | sem_regra
    categoria: str = ""
    descricao: str = ""
    confianca: str = ""
    motivo: str = ""


def _casa(padrao, texto):
    return re.search(padrao, texto, flags=re.IGNORECASE) is not None


def classificar(descricao_banco: str, regras: dict, parcela: str = "", respostas: dict | None = None) -> Classificacao:
    texto = (descricao_banco or "").strip()
    # 1. respostas já dadas pela pessoa valem antes de qualquer regra
    for chave, resposta in (respostas or {}).items():
        if chave.upper() == texto.upper():
            return Classificacao("classificado", resposta["categoria"], resposta.get("descricao", texto), "alta", "resposta")
    # 2. ignorar (pagamento de fatura, transferência entre contas, investimento)
    for padrao in regras.get("ignorar", []):
        if _casa(padrao, texto):
            return Classificacao("ignorar", motivo=f"ignorar: {padrao}")
    # 3. casos que sempre perguntam (ex.: loja on-line que vende de tudo)
    for r in regras.get("perguntar", []):
        if _casa(r["padrao"], texto):
            return Classificacao("perguntar", motivo=r.get("motivo", "Precisa de confirmação"))
    # 4. regras de categoria
    for r in regras.get("regras", []):
        if _casa(r["padrao"], texto):
            descricao = (r.get("descricao") or texto).replace("{parcela}", parcela or "").strip()
            return Classificacao("classificado", r["categoria"], descricao, r.get("confianca", "alta"))
    return Classificacao("sem_regra", motivo="Sem regra para este estabelecimento")
