"""Demo da solução de referência — módulo 03."""

from pathlib import Path

from automation import carregar_solicitacoes, carregar_sops, classificar, executar, recuperar_sop

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    sops = carregar_sops(DATA)
    for solicitacao in carregar_solicitacoes(DATA):
        classificacao = classificar(solicitacao, sops)
        sop, score_sop = recuperar_sop(solicitacao.texto, sops)
        plano, resultado = executar(solicitacao, sops)
        print(f"\n{solicitacao.id}: {solicitacao.texto}")
        print(f"  intenção={classificacao.intencao} conf={classificacao.confianca}")
        print(f"  SOP={sop.arquivo} score={score_sop} aprovacao={plano.requer_aprovacao}")
        print(f"  ferramentas={plano.ferramentas}")
        print(f"  status={resultado.status} sucesso={resultado.sucesso}")
        print(f"  eventos={resultado.eventos}")


if __name__ == "__main__":
    main()
