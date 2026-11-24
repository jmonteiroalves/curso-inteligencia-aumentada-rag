"""Demo da solução de referência — módulo 06."""

import json
from pathlib import Path

from agent import carregar_tarefas, executar_agente

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    for tarefa in carregar_tarefas(DATA):
        estado = executar_agente(str(tarefa["pergunta"]), DATA)
        print(f"\n[{tarefa['id']}] {tarefa['pergunta']}")
        print(f"  rota={estado.rota} status={estado.status}")
        print(f"  resposta={estado.resposta}")
        print(f"  passos={len(estado.passos)} ferramentas={estado.ferramentas_usadas}")
        if estado.motivo:
            print(f"  motivo={estado.motivo}")
        print("  trajetória:")
        for passo in estado.passos:
            print(
                f"    {passo.ferramenta}({passo.entrada[:45]}) -> "
                f"{passo.saida[:60]} ok={passo.ok}"
            )

    estado = executar_agente("Quanto é 12 * 8?", DATA)
    print("\nSerialização do estado:")
    print(json.dumps(estado.to_dict(), ensure_ascii=False, indent=2)[:500])


if __name__ == "__main__":
    main()
