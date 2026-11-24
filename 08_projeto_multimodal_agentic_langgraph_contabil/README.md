# 08 — Multimodal + Agentic + LangGraph contábil

**Resultado:** um fluxo contábil que ingere notas fiscais sintéticas (PNG/PDF), extrai dados com
um sidecar simulando OCR, valida totais e duplicidades, consulta demonstrativos, exige revisão
humana e produz um relatório auditável. A versão de referência em LangGraph fica em
`solucao/langgraph_flow.py`.

> **Analogia:** é uma mesa de auditoria com três pilhas: papel (imagem/PDF), planilha (razão/DRE)
> e manual (política/contrato). O agente não “adivinha” o número: ele cruza as três pilhas,
> marca a divergência com um post-it e chama o controller antes de pagar.

## Arquitetura

```text
PNG/PDF + sidecar OCR ─┐
razão CSV ─────────────┼─> validação (itens × total × razão × duplicidade)
DRE CSV ───────────────┤              │
políticas/contratos ───┘              ├─ divergência → revisão humana
                                      ├─ total > R$ 1.000 → aprovação
                                      └─ relatório + trilha de auditoria
LangGraph: ingerir → extrair → validar → recuperar → revisar → relatório
```

## Micro-etapas

| ID | Tempo | Objetivo | Arquivo | Validação |
|---|---:|---|---|---|
| 8.1 | 25 | Ingerir imagem/PDF com checksum | `src/accounting_agent.py` | 3 notas, checksums e fontes |
| 8.2 | 30 | Extrair número, CNPJ, itens e total | `src/accounting_agent.py` | campos obrigatórios e itens |
| 8.3 | 30 | Validar soma, razão e duplicidade | `src/accounting_agent.py` | NF 1003 bloqueada por R$ 50 |
| 8.4 | 25 | RAG sobre DRE e política | `src/accounting_agent.py` | receita de março com fonte |
| 8.5 | 30 | Grafo LangGraph com revisão | `solucao/langgraph_flow.py` | fluxo de 6 nós executa ou é skip explícito |
| 8.6 | 30 | Relatório e trilha de auditoria | `src/accounting_agent.py` | decisões, evidências e checksums |

**Tempo total:** 2h50.

### Conceito-chave e tarefa prática por etapa

| ID | Conceito-chave | Tarefa prática |
|---|---|---|
| 8.1 | Imagem/PDF é evidência primária; checksum garante rastreio. | Ingerir 3 notas com fonte e hash. |
| 8.2 | OCR/visão é auxiliar e pode errar valores. | Extrair campos e itens do sidecar. |
| 8.3 | Contabilidade fecha por invariantes (soma, razão, duplicidade). | Validar e classificar divergências. |
| 8.4 | DRE e contrato são fontes distintas de RAG. | Responder receita e política com fonte. |
| 8.5 | LangGraph dá estado, nós e revisão explícita. | Executar o fluxo de 6 nós. |
| 8.6 | Auditoria é relatório reproduzível com decisão. | Gerar Markdown e trilha completa. |

## Como executar

```bash
cd 08_projeto_multimodal_agentic_langgraph_contabil

# Dados já gerados; para recriar as imagens/PDFs:
python3 data/gerar_notas.py

python3 src/main.py
python3 solucao/run_demo.py
python3 solucao/evaluate.py
python3 -m unittest discover -s tests -v

# LangGraph (requer dependência opcional instalada)
python3 solucao/langgraph_flow.py
```

## O que implementar

- `# TODO(8.1)` em `ingerir_notas`: sidecar + imagem/PDF + SHA-256.
- `# TODO(8.2)` em `extrair_nota`: campos obrigatórios, itens e total.
- `# TODO(8.3)` em `validar_nota`: soma dos subtotais, total informado, razão, duplicidade e alçada.
- `# TODO(8.4)` em `consultar_contabil`: DRE por mês + trechos de política/contrato.
- `# TODO(8.5)` em `executar_workflow`: pipeline com revisão humana e trilha.
- `# TODO(8.6)` em `gerar_relatorio`: markdown reproduzível e auditável.

### Dicas

1. **OCR não é verdade.** O sidecar é o “texto esperado” do OCR; a imagem/PDF é a fonte primária
   para conferência humana.
2. **Soma de itens ≠ total** é divergência de severidade alta, mesmo que a diferença seja R$ 0,01.
3. **Duplicidade** é detectada no razão por documento; duas linhas para a mesma nota são um alerta.
4. **Alçada** é política: acima de R$ 1.000, o controller aprova; o agente não paga.
5. **Trilha de auditoria** deve conter checksum, valores, divergências, decisão e fonte.
6. **LangGraph** é útil quando há estado, ciclos e branches; para um pipeline linear, funções
   simples bastam. Não use grafo por moda.

## Dados

| Arquivo | Conteúdo |
|---|---|
| `data/notas_fiscais/nf_1001.png/.pdf` | Nimbus, R$ 1.500,00 |
| `data/notas_fiscais/nf_1002.png/.pdf` | Atlas, R$ 780,00 |
| `data/notas_fiscais/nf_1003.png/.pdf` | Nimbus, total R$ 2.450,00; itens somam R$ 2.400,00 |
| `data/notas_fiscais/notas.json` | sidecar de OCR/referência |
| `data/razao.csv` | razão com nota duplicada (1001) e lançamento sem nota (1004) |
| `data/demonstrativos/dre_2026.csv` | receita, custos, despesas e lucro por mês |
| `data/politicas/politica_contabil.md` | alçadas, retenção e trilha |
| `data/contratos/*.md` | valores e prazos dos fornecedores |

## Resultado esperado

- NF 1001: **revisão humana** (total 1.500 > alçada; duplicidade no razão).
- NF 1002: **válida** (780, um lançamento, sem divergência).
- NF 1003: **bloqueada/revisão** (itens 2.400 vs total 2.450; acima da alçada).
- Consulta “Qual foi a receita de março de 2026?” → `R$ 150.000,00`, fonte `dre_2026.csv`.
- Relatório com checksums, divergências, aprovações e eventos do workflow.

## Critério de conclusão

- [ ] As 3 notas são ingeridas com checksum e fonte.
- [ ] `validar_nota` detecta R$ 50,00 de divergência na NF 1003.
- [ ] NF 1001 é marcada como duplicada no razão.
- [ ] Nenhuma nota acima de R$ 1.000 é aprovada automaticamente.
- [ ] A consulta à DRE cita a linha/fonte correta.
- [ ] O relatório contém a trilha `ingestão → extração → validação → consulta → revisão`.
- [ ] O fluxo LangGraph é executado ou reporta a dependência faltante sem quebrar os testes offline.

## Extensões

- Trocar o sidecar por OCR real (`pymupdf`, Tesseract) e comparar campos.
- Usar um modelo de visão via Ollama (`llava`) e medir alucinação de valores.
- Adicionar um nó de aprovação interativa (`interrupt`) no LangGraph.
- Persistir decisões em SQLite com hash do relatório.
- Criar detecção de fraude por fornecedor/valor fora do contrato.
- Exportar o relatório em PDF assinado e comparar checksums.
