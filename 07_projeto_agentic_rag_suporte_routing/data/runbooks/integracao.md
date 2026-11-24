# Runbook — Integração

1. Verifique status da API, filas e últimos eventos processados.
2. Se o impacto for de todos os clientes ou houver indisponibilidade total, escale como P1.
3. Para webhook atrasado, reprocesse eventos de forma idempotente e confirme a entrega.
4. Se o serviço estiver parado ou houver risco de perda de dados, faça handoff para engenharia.
5. Comunique o cliente com horário e próxima atualização.

Ferramentas: `verificar_status_integracao`, `reprocessar_evento`, `escalar_engenharia`.
