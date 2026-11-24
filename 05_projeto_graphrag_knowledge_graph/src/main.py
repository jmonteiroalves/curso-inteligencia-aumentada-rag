"""Demo do esqueleto — módulo 05."""

from pathlib import Path

from graph_rag import carregar_gazetteer, carregar_textos, construir_grafo

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    print("Entidades:", len(carregar_gazetteer(DATA)))
    print("Textos:", [fonte for fonte, _ in carregar_textos(DATA)])
    try:
        grafo = construir_grafo(DATA)
        print("Nós:", len(grafo.entidades), "Arestas:", len(grafo.triplas))
    except NotImplementedError as exc:
        print(f"\nAinda não implementado: {exc}")
        print("Sequência: TODO(5.1) → 5.2 → 5.3 → 5.4 → 5.5 → 5.6.")


if __name__ == "__main__":
    main()
