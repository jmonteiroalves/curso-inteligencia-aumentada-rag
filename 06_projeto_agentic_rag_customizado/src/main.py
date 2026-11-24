"""Demo do esqueleto — módulo 06."""

from pathlib import Path

from agent import carregar_docs, carregar_tarefas, classificar_rota

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    print("Docs:", [fonte for fonte, _ in carregar_docs(DATA)])
    print("Tarefas:", len(carregar_tarefas(DATA)))
    try:
        for pergunta in ("Qual o limite de alimentação?", "Quanto é 12 * 8?", "Olá!"):
            print(pergunta, "->", classificar_rota(pergunta))
    except NotImplementedError as exc:
        print(f"\nAinda não implementado: {exc}")
        print("Sequência: TODO(6.1) → 6.2 → 6.3 → 6.4 → 6.5 → 6.6.")


if __name__ == "__main__":
    main()
