# 03 — SLM + RAG + automação de processos

**Resultado:** um agente de automação interna que classifica solicitações, recupera o procedimento
operacional padrão (SOP), monta um plano JSON validado e simula a execução com aprovação humana.

> **Analogia:** o SLM é o recepcionista que ouve o pedido e escolhe a fila; o RAG é o manual de
> procedimentos; o validador é o supervisor que confere se o atendente não inventou uma etapa;
> o simulador é o ensaio antes de apertar o botão real.

## Arquitetura

```text
solicitação
  ├─> classificador (SLM/rules) → intenção + confiança
  ├─> retrieval de SOP         → procedimento + ferramentas permitidas
  ├─> planejador               → JSON com passos e aprovação
  ├─> validador de plano       → ferramentas, campos, risco
  └─> simulador                → eventos, sucesso, aprovação pendente
```

## Micro-etapas

| ID | Tempo | Objetivo | Arquivo | Validação |
|---|---:|---|---|---|
| 3.1 | 20 | Mapear intenções, SOPs e ferramentas | `data/sops.json` | 4 intenções + fallback desconhecido |
| 3.2 | 25 | Classificar 8 solicitações com confiança | `src/automation.py` | ≥ 7/8 corretas; baixa confiança escala |
| 3.3 | 20 | Recuperar o SOP correto | `src/automation.py` | SOP esperado no top-1 |
| 3.4 | 25 | Montar e validar plano JSON | `src/automation.py` | ferramenta inexistente/campo vazio rejeitados |
| 3.5 | 30 | Simular execução e métricas | `src/automation.py` | sucesso, aprovações e escalonamentos medidos |

**Tempo total:** 2h00.

### Conceito-chave e tarefa prática por etapa

| ID | Conceito-chave | Tarefa prática |
|---|---|---|
| 3.1 | Taxonomia é a primeira interface do agente. | Mapear 4 intenções, SOPs e ferramentas. |
| 3.2 | SLM é um classificador; confiança decide quando escalar. | Classificar 8 pedidos com fallback. |
| 3.3 | SOP é a política local recuperável. | Rankear e recuperar o runbook correto. |
| 3.4 | Plano é contrato: passos, ferramentas e risco. | Validar JSON e rejeitar ferramenta inventada. |
| 3.5 | Simulação segura evita efeito colateral real. | Executar leituras e bloquear mutações sem aprovação. |

## Como executar

```bash
cd 03_projeto_slm_rag_automacao
python3 src/main.py
python3 solucao/run_demo.py
python3 solucao/evaluate.py
python3 -m unittest discover -s tests -v
```

Opcional com Ollama:

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.2:3b
# ajuste OLLAMA_BASE_URL e use solucao/llm_optional.py como extensão
```

## O que implementar

- `# TODO(3.2)` em `classificar`: pontuação por palavras-chave com confiança e fallback.
- `# TODO(3.3)` em `recuperar_sop`: ranking lexical do procedimento.
- `# TODO(3.4)` em `montar_plano`/`validar_plano`: JSON tipado, ferramentas permitidas, limite e aprovação.
- `# TODO(3.5)` em `simular`: efeitos colaterais mockados e bloqueio de ação mutante sem aprovação.

### Dicas

1. **Confiança não é probabilidade calibrada.** Aqui ela serve para decidir quando escalar.
2. Um plano é um **contrato**: intenção, SOP, passos, ferramentas, risco, aprovação.
3. Valide a lista de ferramentas contra o SOP. Um LLM pode inventar `transferir_dinheiro`.
4. Separe ferramentas **read-only** (`validar_despesa`) de **mutantes** (`criar_reembolso`).
5. A simulação deve ser determinística para permitir testes e replay.

## Dados

| Arquivo | Conteúdo |
|---|---|
| `data/sops.json` | 4 procedimentos, palavras-chave, ferramentas e limites |
| `data/sops/*.md` | versão narrativa dos procedimentos |
| `data/solicitacoes.json` | 8 solicitações rotuladas, incluindo uma ambígua |

Regras de negócio sintéticas:

- reembolso acima de **R$ 500** exige gestor;
- compra acima de **R$ 1.000** exige gestor;
- onboarding cria usuário e agenda sessão;
- acesso segue menor privilégio;
- intenção desconhecida vai para `escalar_suporte`.

## Critério de conclusão

- [ ] `evaluate.py` reporta acurácia de intenção ≥ 7/8 e SOP top-1 = 100% nos casos rotulados.
- [ ] Um plano com ferramenta inventada é rejeitado.
- [ ] Reembolso de R$ 620 termina em `aguardando_aprovacao`, sem `criar_reembolso`.
- [ ] A solicitação ambígua é escalada, não “chutada”.
- [ ] Você explica por que o classificador é apenas a primeira etapa, não o sistema inteiro.

## Extensões

- Use Ollama com `format=json` e compare a calibração com a baseline.
- Adicione idempotência por `solicitacao_id` para não criar dois reembolsos.
- Crie uma fila de aprovação com estados `pendente`, `aprovado`, `rejeitado`.
- Adicione um teste adversarial com pedido de “ignorar as regras”.
- Meça custo/latência por solicitação e defina orçamento por lote.
