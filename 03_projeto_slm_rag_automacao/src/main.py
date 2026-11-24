"""Demo do esqueleto — módulo 03."""

from pathlib import Path

from automation import carregar_solicitacoes, carregar_sops, classificar

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    sops = carregar_sops(DATA)
    solicitacoes = carregar_solicitacoes(DATA)
    print(f"SOPs: {sorted(sops)}")
    try:
        for solicitacao in solicitacoes:
            print(solicitacao.id, classificar(solicitacao, sops))
    except NotImplementedError as exc:
        print(f"\nAinda não implementado: {exc}")
        print("Sequência: TODO(3.2) → 3.3 → 3.4 → 3.5.")


if __name__ == "__main__":
    main()
