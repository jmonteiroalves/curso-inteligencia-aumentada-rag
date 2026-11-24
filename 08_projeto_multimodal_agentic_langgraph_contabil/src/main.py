"""Demo do esqueleto — módulo 08."""

from pathlib import Path

from accounting_agent import carregar_lancamentos, carregar_sidecar, executar_workflow

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    print("Sidecar:", len(carregar_sidecar(DATA)))
    print("Lançamentos:", len(carregar_lancamentos(DATA)))
    try:
        resultado = executar_workflow(DATA)
        print("Status:", resultado.status)
        print(resultado.relatorio[:500])
    except NotImplementedError as exc:
        print(f"\nAinda não implementado: {exc}")
        print("Sequência: TODO(8.1) → 8.2 → 8.3 → 8.4 → 8.5 → 8.6.")


if __name__ == "__main__":
    main()
