"""Demo da solução de referência — módulo 07."""

from pathlib import Path

from support_agent import carregar_clientes, carregar_tickets, executar_ticket

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    clientes = carregar_clientes(DATA)
    for ticket in carregar_tickets(DATA):
        cliente = clientes[ticket.cliente_id]
        resultado = executar_ticket(ticket, cliente, DATA)
        r = resultado.roteamento
        print(f"\n{ticket.id} | {ticket.texto}")
        print(
            f"  categoria={r.categoria} prioridade={r.prioridade} fila={r.fila} "
            f"SLA={r.sla_horas}h conf={r.confianca}"
        )
        print(f"  runbook={resultado.runbook}")
        print(f"  ações={[a.ferramenta for a in resultado.acoes]}")
        print(f"  status={resultado.status} motivo={resultado.motivo_escalonamento}")
        print(f"  eventos={resultado.eventos}")


if __name__ == "__main__":
    main()
