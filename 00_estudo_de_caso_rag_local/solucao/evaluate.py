"""Avaliação do RAG local contra o golden set (módulo 00)."""

from __future__ import annotations

import json
from pathlib import Path

from rag_solution import RAGIndex, carregar_documentos

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"


def main() -> None:
    perguntas = [
        json.loads(linha)
        for linha in (DATA / "perguntas.jsonl").read_text(encoding="utf-8").splitlines()
        if linha.strip()
    ]
    indice = RAGIndex(carregar_documentos(DATA)).index()

    acertos = 0
    respondiveis = 0
    abstencoes_corretas = 0
    fora_do_corpus = 0
    citacoes = 0
    detalhes: list[str] = []

    for item in perguntas:
        resposta = indice.answer(item["pergunta"], top_k=3)
        hits = indice.search(item["pergunta"], top_k=3)
        fontes_top3 = {hit.chunk.fonte for hit in hits}
        esperado = bool(item.get("respondivel", True))

        if esperado:
            respondiveis += 1
            ok = bool(set(item["fontes"]) & fontes_top3)
            acertos += int(ok)
            if not resposta.absteve and resposta.fontes:
                citacoes += 1
            detalhes.append(
                f"{item['id']} hit@3={'ok' if ok else 'FALHOU'} "
                f"absteve={resposta.absteve} fontes={resposta.fontes}"
            )
        else:
            fora_do_corpus += 1
            abstencoes_corretas += int(resposta.absteve)
            detalhes.append(f"{item['id']} fora_do_corpus absteve={resposta.absteve}")

    hit3 = acertos / max(1, respondiveis)
    abstencao = abstencoes_corretas / max(1, fora_do_corpus)
    citacao = citacoes / max(1, respondiveis)

    print("== Avaliação RAG local ==")
    print(f"hit@3.............. {hit3:.2%} ({acertos}/{respondiveis})")
    print(f"citação............ {citacao:.2%}")
    print(f"abstenção correta.. {abstencao:.2%} ({abstencoes_corretas}/{fora_do_corpus})")
    print("\nDetalhes:")
    print("\n".join(f"- {linha}" for linha in detalhes))
    if hit3 < 0.8 or abstencao < 1.0:
        raise SystemExit("Critério não atingido: ajuste retrieval/threshold e tente novamente.")


if __name__ == "__main__":
    main()
