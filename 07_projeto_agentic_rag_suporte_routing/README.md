# 07 — Agentic RAG para suporte e routing

**Resultado:** um agente de triagem que classifica tickets, roteia para a fila correta, recupera o
runbook do domínio, planeja ações e aplica aprovação humana e escalonamento antes de qualquer
mutação.

> **Analogia:** o agente é o supervisor de um call center. Ele lê o chamado, escolhe a fila, abre
> o manual daquela fila, autoriza o procedimento padrão e — quando o caso é grave ou envolve
> dinheiro — chama um humano antes de apertar o botão.

## Arquitetura

```text
ticket + cliente
  └─> classificação (categoria/prioridade/confiança)
        └─> routing (fila + SLA)
              └─> runbook (RAG)
                    └─> plano de ações
                          ├─ read-only → executa
                          ├─ mutação → aprovação humana
                          └─ P1/segurança → handoff
                                └─ métricas operacionais
```

## Micro-etapas

| ID | Tempo | Objetivo | Arquivo | Validação |
|---|---:|---|---|---|
| 7.1 | 20 | Taxonomia e tickets rotulados | `data/tickets.jsonl` | 4 categorias e 10 tickets |
| 7.2 | 25 | Classificar, priorizar e rotear | `src/support_agent.py` | P1 crítico em ≤1 passo |
| 7.3 | 25 | Runbooks como ferramentas | `src/support_agent.py` | runbook correto por domínio |
| 7.4 | 30 | Ações com aprovação | `src/support_agent.py` | reembolso nunca executa sozinho |
| 7.5 | 20 | Política de escalonamento | `src/support_agent.py` | 3 gatilhos testados |
| 7.6 | 30 | Simulador e métricas | `solucao/evaluate.py` | contenção, handoff e SLA risk |

**Tempo total:** 2h30.

### Conceito-chave e tarefa prática por etapa

| ID | Conceito-chave | Tarefa prática |
|---|---|---|
| 7.1 | Taxonomia de ticket define fila, SLA e risco. | Rotular 10 tickets em 4 domínios. |
| 7.2 | Prioridade é política operacional, não sentimento. | Classificar, priorizar e rotear. |
| 7.3 | Runbook é a ferramenta local do domínio. | Recuperar o procedimento com fallback. |
| 7.4 | Mutação exige aprovação; handoff é sucesso. | Planejar e simular ações com gate. |
| 7.5 | Escalonamento tem gatilhos explícitos. | Testar P1, segurança e serviço parado. |
| 7.6 | Métrica sozinha não prova qualidade. | Medir contenção, handoff e pendências. |

## Como executar

```bash
cd 07_projeto_agentic_rag_suporte_routing
python3 src/main.py
python3 solucao/run_demo.py
python3 solucao/evaluate.py
python3 -m unittest discover -s tests -v
```

## O que implementar

- `# TODO(7.2)` em `classificar_ticket`, `priorizar` e `rotear`.
- `# TODO(7.3)` em `recuperar_runbook`.
- `# TODO(7.4)` em `planejar_acoes` e `executar_ticket`.
- `# TODO(7.5)` em `deve_escalar`.
- `# TODO(7.6)` em `solucao/evaluate.py`: contenção, handoff, aprovação e SLA.

### Dicas

1. **Segurança vence acesso.** “Acesso indevido” é incidente de segurança, não reset de senha.
2. **P1 é fila, não frase.** Prioridade define SLA, escalation e nível de resposta.
3. **Runbook é a política local.** A ferramenta certa vem do runbook, não da imaginação do LLM.
4. **Mutação exige aprovação.** Reembolso, bloqueio de conta e exclusão nunca são automáticos.
5. **Handoff é sucesso operacional**, não falha do agente.
6. **Métrica de contenção** só vale junto com segurança e satisfação; não otimize um número só.

## Dados

| Arquivo | Conteúdo |
|---|---|
| `data/tickets.jsonl` | 10 tickets sintéticos com categoria, prioridade e status esperados |
| `data/clientes.json` | 5 clientes e planos |
| `data/runbooks/*.md` | procedimentos para cobrança, acesso, integração, segurança e fallback |

Categorias: `cobranca`, `acesso`, `integracao`, `seguranca`.
Prioridades: `P1` (1h), `P2` (8h), `P3` (24h), com SLA menor para Enterprise em P1.

## Critério de conclusão

- [ ] Classificação e prioridade ≥ 9/10 no conjunto rotulado.
- [ ] O ticket de segurança é roteado para `seguranca`, nunca para reset de senha.
- [ ] Reembolso termina em `aguardando_aprovacao` e não executa a mutação.
- [ ] P1 e serviço parado disparam handoff com motivo.
- [ ] `evaluate.py` mostra contenção, handoffs, aprovações e risco de SLA.
- [ ] Você explica por que “resolver tudo sozinho” não é o objetivo.

## Extensões

- Implemente uma fila real com estados e SLA em SQLite.
- Adicione um classificador SLM e compare com as regras.
- Crie uma política de “cliente Enterprise” com prioridade e comunicação diferentes.
- Adicione idempotência por ticket para não abrir dois reembolsos.
- Use LangGraph para modelar `triagem → runbook → aprovação → handoff`.
- Adicione um teste de prompt injection no corpo do ticket.
