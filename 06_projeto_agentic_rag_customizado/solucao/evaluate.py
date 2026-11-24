"""Avaliação do agente e das trajetórias (módulo 06)."""

from __future__ import annotations

from pathlib import Path

from agent import calcular, carregar_tarefas, executar_agente

DATA = Path(__file__).resolve().parent.parent / "data"
FERRAMENTAS_REAIS = {"buscar_politicas", "calcular"}


def main() -> None:
    tarefas = carregar_tarefas(DATA)
    acertos_finais = 0
    acertos_ferramentas = 0
    citacoes_ok = 0
    total_passos = 0

    for tarefa in tarefas:
        estado = executar_agente(str(tarefa["pergunta"]), DATA)
        usadas = {p.ferramenta for p in estado.passos} & FERRAMENTAS_REAIS
        esperadas = set(tarefa["ferramentas_esperadas"])
        termos = [str(t).lower() for t in tarefa["termos_esperados"]]
        resposta = estado.resposta.lower()
        ok_final = estado.status == tarefa["status_esperado"] and all(t in resposta for t in termos)
        ok_ferramentas = usadas == esperadas
        acertos_finais += int(ok_final)
        acertos_ferramentas += int(ok_ferramentas)
        total_passos += len(estado.passos)
        if estado.evidencias:
            citacoes_ok += int("[" in estado.resposta)
        print(
            f"{'ok' if ok_final and ok_ferramentas else 'FALHOU'} | {tarefa['id']} "
            f"status={estado.status:<18} ferramentas={sorted(usadas)} passos={len(estado.passos)}"
        )
        print(f"   {estado.resposta[:140]}")

    # Testes de segurança do cálculo.
    seguranca = 0
    for expressao in ("__import__('os')", "2 ** 10", "10 / 0", "2;3"):
        try:
            calcular(expressao)
        except ValueError:
            seguranca += 1

    estado_zero = executar_agente("Quanto é 2 + 2?", DATA, max_passos=0)
    print("\n== Segurança e orçamento ==")
    print(f"cálculos maliciosos bloqueados: {seguranca}/4")
    print(f"max_passos=0: status={estado_zero.status}")
    print(f"acurácia final: {acertos_finais}/{len(tarefas)}")
    print(f"ferramentas corretas: {acertos_ferramentas}/{len(tarefas)}")
    print(f"citações em respostas com retrieval: {citacoes_ok}")
    print(f"passos médios: {total_passos / len(tarefas):.2f}")

    if (
        acertos_finais < 7
        or acertos_ferramentas < 7
        or seguranca < 4
        or estado_zero.status != "orcamento_excedido"
    ):
        raise SystemExit("Critério de avaliação não atingido")


if __name__ == "__main__":
    main()
