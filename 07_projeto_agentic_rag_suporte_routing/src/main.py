"""Demo do esqueleto — módulo 07."""

from pathlib import Path

from support_agent import carregar_clientes, carregar_tickets, classificar_ticket

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    tickets = carregar_tickets(DATA)
    clientes = carregar_clientes(DATA)
    print(f"Tickets: {len(tickets)} | clientes: {len(clientes)}")
    try:
        for ticket in tickets:
            print(ticket.id, classificar_ticket(ticket))
    except NotImplementedError as exc:
        print(f"\nAinda não implementado: {exc}")
        print("Sequência: TODO(7.2) → 7.3 → 7.4 → 7.5 → 7.6.")


if __name__ == "__main__":
    main()
