"""Avaliação de classificação, planos e simulação (módulo 03)."""

from __future__ import annotations

from pathlib import Path

from automation import (
    PlanoAcao,
    carregar_solicitacoes,
    carregar_sops,
    classificar,
    executar,
    recuperar_sop,
    validar_plano,
)

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    sops = carregar_sops(DATA)
    solicitacoes = carregar_solicitacoes(DATA)
    acertos_intencao = 0
    acertos_sop = 0
    planos_validos = 0
    concluidos = 0
    aprovacoes = 0
    escalados = 0

    for solicitacao in solicitacoes:
        classificacao = classificar(solicitacao, sops)
        sop, _ = recuperar_sop(solicitacao.texto, sops)
        acertos_intencao += int(classificacao.intencao == solicitacao.intencao_esperada)
        if classificacao.intencao != "desconhecido":
            sop = sops[classificacao.intencao]
        acertos_sop += int(sop.arquivo == solicitacao.sop_esperado)
        try:
            plano, resultado = executar(solicitacao, sops)
            validar_plano(plano, sops)
            planos_validos += 1
            concluidos += int(resultado.sucesso)
            aprovacoes += int(resultado.status == "aguardando_aprovacao")
            escalados += int(resultado.status == "escalado")
            print(
                f"{solicitacao.id} intenção={classificacao.intencao:<12} "
                f"sop={sop.arquivo:<16} status={resultado.status}"
            )
        except ValueError as exc:
            print(f"{solicitacao.id} PLANO INVÁLIDO: {exc}")

    # Caso sintético de aprovação: reembolso acima de R$ 500.
    from automation import Solicitacao

    caro = Solicitacao("teste", "Reembolso de hotel R$ 620 com nota fiscal", valor=620.0)
    plano, resultado = executar(caro, sops)
    print(f"\nTeste de aprovação: {plano.to_dict()['motivo_aprovacao']} status={resultado.status}")
    if resultado.status != "aguardando_aprovacao":
        raise SystemExit("Reembolso acima do limite deveria aguardar aprovação")

    precisao = acertos_intencao / len(solicitacoes)
    print("\n== Avaliação ==")
    print(f"intenção............ {acertos_intencao}/{len(solicitacoes)} ({precisao:.0%})")
    print(f"SOP top-1........... {acertos_sop}/{len(solicitacoes)}")
    print(f"planos válidos...... {planos_validos}/{len(solicitacoes)}")
    print(f"concluídos.......... {concluidos}")
    print(f"aprovações.......... {aprovacoes}")
    print(f"escalonamentos...... {escalados}")
    if acertos_intencao < 7 or acertos_sop < len(solicitacoes) or planos_validos < len(solicitacoes):
        raise SystemExit("Critério de avaliação não atingido")


if __name__ == "__main__":
    main()
