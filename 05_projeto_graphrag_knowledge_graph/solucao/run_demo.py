"""Demo da solução de referência — módulo 05."""

from pathlib import Path

from graph_rag import construir_grafo, responder_hibrido, resumo_comunidades

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    grafo = construir_grafo(DATA)
    print(f"Grafo: {len(grafo.entidades)} nós, {len(grafo.triplas)} arestas")
    print("Top graus:", sorted(((grafo.grau(n), n) for n in grafo.entidades), reverse=True)[:5])

    perguntas = [
        "Quem lidera o projeto que usa Qdrant?",
        "Qual instituto financia o projeto que usa LangGraph?",
        "Quem trabalha na empresa parceira da Nimbus Cloud?",
        "Qual tecnologia o projeto liderado por Beatriz Nunes usa?",
        "Quem Marina Costa mentora e onde essa pessoa trabalha?",
    ]
    for pergunta in perguntas:
        resposta = responder_hibrido(grafo, pergunta, DATA)
        print(f"\nP: {pergunta}")
        print(f"R: {resposta.resposta} (score={resposta.score}, absteve={resposta.absteve})")
        for caminho in resposta.caminhos:
            print(f"  caminho: {caminho}")
        print(f"  fontes: {resposta.fontes}")
        for trecho in resposta.contexto_textual[:2]:
            print(f"  texto: [{trecho.fonte}] {trecho.texto[:100]}")

    print("\nComunidades:")
    for resumo in resumo_comunidades(grafo):
        print(resumo)


if __name__ == "__main__":
    main()
