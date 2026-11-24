"""Avaliação offline do serviço RAG (módulo 01)."""

from __future__ import annotations

import json
from pathlib import Path

from rag_core import RagService

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"


def main() -> None:
    servico = RagService(DATA)
    servico.carregar_diretorio()
    itens = [
        json.loads(linha)
        for linha in (DATA / "perguntas.jsonl").read_text(encoding="utf-8").splitlines()
        if linha.strip()
    ]
    respondiveis = [i for i in itens if i.get("respondivel", True)]
    fora = [i for i in itens if not i.get("respondivel", True)]
    acertos = 0
    citacoes = 0
    abstencoes = 0

    for item in itens:
        resultado = servico.query(item["pergunta"], top_k=3)
        hits = servico.search(item["pergunta"], top_k=3)
        if item.get("respondivel", True):
            acertos += int(bool(set(item["fontes"]) & {h.chunk.fonte for h in hits}))
            citacoes += int(not resultado.absteve and bool(resultado.fontes))
        else:
            abstencoes += int(resultado.absteve)

    print("== Avaliação LLMOps ==")
    print(f"hit@3............ {acertos / len(respondiveis):.2%}")
    print(f"citação.......... {citacoes / len(respondiveis):.2%}")
    print(f"abstenção........ {abstencoes / max(1, len(fora)):.2%}")
    print(f"eventos.......... {len(servico.eventos)}")
    if acertos / len(respondiveis) < 0.8:
        raise SystemExit("hit@3 abaixo de 0,8")


if __name__ == "__main__":
    main()
