# 01 — LLMOps: deploy de um serviço RAG

**Resultado:** uma API RAG com ingestão idempotente, citações, avaliação offline, logs estruturados
e empacotamento Docker. O foco é **operação**, não apenas “fazer a resposta sair”.

> **Analogia:** LLMOps é a cozinha industrial de um restaurante. A receita (RAG) já existe; agora
> precisamos de estoque rastreável, porções padronizadas, controle de qualidade, ficha técnica e
> capacidade de reabrir depois de uma falha.

## Arquitetura

```text
POST /ingest ──> validação ──> checksum ──> índice em memória
                                    │
                                    └─ idempotência (mesmo doc não duplica)
POST /query ───> busca top-k ───> resposta + fontes + latência + request_id
                                    │
                                    └─ log JSON (observabilidade)
GET /health  ───> documentos, chunks, versão
```

## Micro-etapas

| ID | Tempo | Objetivo | Arquivo | Validação |
|---|---:|---|---|---|
| 1.1 | 20 | Definir contrato Pydantic da API e `/health` | `src/app.py` | modelos importam; health pronto |
| 1.2 | 30 | Ingestão idempotente + chunking | `src/rag_core.py` | reingestão retorna `ignorados > 0` e sem chunks duplicados |
| 1.3 | 30 | `POST /query` com citações e latência | `src/app.py` | resposta contém fontes e `latencia_ms` |
| 1.4 | 25 | Golden set e avaliação offline | `solucao/evaluate.py` | hit@3 ≥ 0,8 |
| 1.5 | 20 | Logs estruturados com `request_id` | `src/rag_core.py` | uma consulta gera log JSON válido |
| 1.6 | 30 | Dockerfile e configuração | `Dockerfile` | build e `/health` respondem |

**Tempo total:** 2h35.

### Conceito-chave e tarefa prática por etapa

| ID | Conceito-chave | Tarefa prática |
|---|---|---|
| 1.1 | API é contrato; `health` verifica processo e índice, não o LLM. | Definir modelos e rota de saúde. |
| 1.2 | Idempotência começa com chave + checksum. | Ingerir o mesmo lote sem duplicar chunks. |
| 1.3 | Resposta precisa de citação, score e latência. | Implementar `/query` e resposta extrativa. |
| 1.4 | Golden set é o teste de regressão do RAG. | Rodar hit@3 e registrar falhas. |
| 1.5 | Observabilidade é um evento estruturado por consulta. | Emitir log JSON com request_id e top_k. |
| 1.6 | Deploy precisa ser reproduzível e ter healthcheck. | Empacotar em Docker e validar `/health`. |

## Como executar

```bash
cd 01_projeto_llmops_deploy_rag

python3 src/main.py                    # esqueleto
python3 solucao/run_demo.py            # referência sem servidor
python3 solucao/evaluate.py            # avaliação offline
python3 -m unittest discover -s tests -v

# API de referência (requer fastapi/uvicorn)
uvicorn solucao.app_solution:app --reload --app-dir . --port 8000
curl localhost:8000/health
curl -X POST localhost:8000/query \
  -H 'content-type: application/json' \
  -d '{"pergunta":"Quantos usuários o plano Pro permite?","top_k":3}'

# Container
docker build -t curso-rag-01 .
docker run --rm -p 8000:8000 curso-rag-01
```

## Contrato da API

| Método | Rota | Entrada | Saída |
|---|---|---|---|
| GET | `/health` | — | status, docs, chunks, versão |
| POST | `/ingest` | `{"documentos":[{id,titulo,texto,fonte}]}` | novos, atualizados, ignorados |
| POST | `/query` | `{"pergunta": str, "top_k": int}` | resposta, fontes, score, latência, request_id |

## O que implementar

- `# TODO(1.1)` em `src/app.py`: modelos Pydantic, `/health` e injeção do serviço.
- `# TODO(1.2)` em `src/rag_core.py`: checksum, ingestão idempotente e rebuild do índice.
- `# TODO(1.3)` em `src/rag_core.py`: busca híbrida, resposta extrativa e citações.
- `# TODO(1.5)` em `src/rag_core.py`: evento JSON por consulta.
- `# TODO(1.6)` no `Dockerfile`: copiar dados, expor porta e healthcheck.

### Dicas

1. Idempotência começa com uma **chave estável**: `id` do documento + `sha256` do conteúdo.
2. Não reconstrua o índice inteiro a cada chunk; reconstrua ao final de cada lote.
3. A resposta da API deve ser um contrato, não um `dict` solto.
4. Meça latência no servidor (`perf_counter`) e registre o `top_k` usado.
5. Um healthcheck não deve chamar o LLM; ele verifica o processo e o índice.

## Dados

| Arquivo | Conteúdo | Fatos-âncora |
|---|---|---|
| `base_conhecimento/produto.md` | produto SaaS | Aurora Flow, 3 módulos |
| `base_conhecimento/planos.md` | preços | Pro: 25 usuários; Enterprise: ilimitado |
| `base_conhecimento/sla.md` | suporte | P1 15 min; P2 2h |
| `base_conhecimento/onboarding.md` | implantação | 14 dias; 2 workshops |

O golden set (`data/perguntas.jsonl`) cobre fatos, uma pergunta multi-documento e uma fora do corpus.

## Critério de conclusão

- [ ] Ingerir o mesmo lote duas vezes não aumenta o número de chunks.
- [ ] Toda resposta não abstenha contém `fontes` não vazias.
- [ ] O log de consulta é JSON parseável e tem `request_id`, `latencia_ms` e `score`.
- [ ] `docker build` conclui e `/health` retorna `status=ok`.
- [ ] Você consegue explicar o que acontece se dois processos ingerirem o mesmo documento.

## Extensões

- Troque o índice em memória por Qdrant, preservando o contrato da API.
- Adicione `Idempotency-Key` no header e um cache de respostas.
- Introduza um limite de taxa por IP com um middleware.
- Adicione `prompt_tokens`, `completion_tokens` e custo estimado ao log.
- Faça um teste de contrato com `httpx.ASGITransport` (sem subir servidor).
