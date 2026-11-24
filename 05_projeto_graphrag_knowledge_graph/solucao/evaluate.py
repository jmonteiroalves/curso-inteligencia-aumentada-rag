"""Avaliação do GraphRAG (módulo 05)."""

from __future__ import annotations

from pathlib import Path

from graph_rag import (
    construir_grafo,
    exportar_cypher,
    responder_hibrido,
    resumo_comunidades,
)

DATA = Path(__file__).resolve().parent.parent / "data"

CASOS = [
    ("Quem lidera o projeto que usa Qdrant?", {"Marina Costa"}),
    ("Qual instituto financia o projeto que usa LangGraph?", {"Instituto Horizonte"}),
    ("Quem trabalha na empresa parceira da Nimbus Cloud?", {"Marina Costa", "Rafael Alves", "Lucas Ferreira"}),
    ("Qual tecnologia o projeto liderado por Beatriz Nunes usa?", {"Kafka"}),
    ("Quem Marina Costa mentora e onde essa pessoa trabalha?", {"Aurora Tech"}),
]


def main() -> None:
    grafo = construir_grafo(DATA)
    acertos = 0
    print(f"Nós: {len(grafo.entidades)} | arestas: {len(grafo.triplas)}")

    for pergunta, esperado in CASOS:
        r = responder_hibrido(grafo, pergunta, DATA)
        obtido = {x.strip() for x in r.resposta.split(",")}
        ok = esperado.issubset(obtido) and not r.absteve and bool(r.fontes)
        acertos += int(ok)
        print(f"{'ok' if ok else 'FALHOU'} | {pergunta}")
        print(f"   resposta={r.resposta} score={r.score} fontes={r.fontes}")
        if r.caminhos:
            print(f"   caminho={r.caminhos[0]}")

    cypher = exportar_cypher(grafo)
    comunidades = resumo_comunidades(grafo)
    membros = sum(int(c["tamanho"]) for c in comunidades)
    print(f"\nCypher: {cypher.count('MERGE')} operações MERGE")
    print(f"Comunidades: {len(comunidades)} | membros={membros}")

    falhas = []
    if acertos < len(CASOS):
        falhas.append(f"acertos={acertos}/{len(CASOS)}")
    if len(grafo.entidades) < 20 or len(grafo.triplas) < 15:
        falhas.append("grafo menor que o esperado")
    if cypher.count("MERGE") < len(grafo.entidades) + len(grafo.triplas):
        falhas.append("Cypher incompleto")
    if membros != len(grafo.entidades):
        falhas.append("comunidades não cobrem todos os nós")
    if falhas:
        raise SystemExit("Falhas: " + "; ".join(falhas))
    print("Critérios de avaliação atingidos.")


if __name__ == "__main__":
    main()
