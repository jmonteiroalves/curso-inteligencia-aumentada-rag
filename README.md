# Inteligência Aumentada com RAG, GraphRAG e Agentic RAG

Curso prático, local-first e **Learn by Building** para dominar recuperação aumentada, grafos de conhecimento e agentes.
Cada módulo é uma sequência de micro-etapas de **15–30 minutos**, com um artefato executável e um critério de validação.

> **Tese do curso:** um LLM sozinho é um orador brilhante sem acesso aos arquivos da empresa.
> RAG dá a ele uma biblioteca; GraphRAG, um mapa das relações; Agentic RAG, um gerente que decide
> quais ferramentas usar, verifica o resultado e pede aprovação antes de agir.

## Por que este formato funciona

- **Blocos curtos:** você sempre termina com algo rodando, mesmo em uma agenda apertada.
- **Esqueletos com `TODO:`:** você implementa a lógica central; não apenas executa um notebook.
- **Soluções de referência:** `solucao/` existe para desbloquear, comparar e revisar — não para copiar.
- **Dados sintéticos:** nenhuma dependência de APIs pagas, buscas externas ou dados pessoais reais.
- **Fallback offline:** as soluções rodam sem LLM. Integrações com Ollama/OpenAI são opcionais.

## Comece em 10 minutos

```bash
cd curso-inteligencia-aumentada-rag
python3 --version                  # 3.11+
cp .env.example .env               # opcional; não coloque chaves reais em git
python3 scripts/validate_repo.py   # estrutura, datasets e TODOs
make test                          # 51 micro-etapas cobertas por smoke tests

cd 00_estudo_de_caso_rag_local
python3 solucao/run_demo.py        # referência funcional
python3 src/main.py                # seu esqueleto (deve apontar o TODO atual)
```

Se `make` não existir, rode:

```bash
for d in 0*_*/; do (cd "$d" && python3 -m unittest discover -s tests -v) || exit 1; done
```

> Os testes são executados **por módulo**. Cada projeto tem seu próprio pacote `solucao/`;
> rodar todos em um único processo de pytest pode misturar os pacotes. Use `make test` ou
> entre na pasta do módulo e rode `python3 -m unittest` (ou `pytest`).

## Setup completo (opcional)

### Com `uv` (recomendado)

```bash
uv venv --python 3.11
source .venv/bin/activate
uv sync
# ou: uv pip install -r requirements.txt
```

### Com `pip`

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Serviços locais

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.2:3b
docker compose exec ollama ollama pull nomic-embed-text

# Perfis modulares
docker compose --profile vectors up -d qdrant
docker compose --profile pgvector up -d postgres
docker compose --profile graph up -d neo4j
```

| Serviço | URL local | Uso no curso |
|---|---|---|
| Ollama | `http://localhost:11434` | SLMs, chat e visão opcionais |
| Qdrant | `http://localhost:6333` | Módulos 00, 01, 04, 08 |
| PostgreSQL + pgvector | `localhost:5432` | Alternativa vetorial no módulo 01 |
| Neo4j Community | `http://localhost:7474` | Exportação do grafo no módulo 05 |

Os demos **não exigem** esses serviços. Eles usam implementações determinísticas em memória para que o
conceito seja o foco; a integração real é uma etapa de extensão.

## Mapa de dependências

```text
00 RAG local ──────────────┬──> 01 LLMOps / deploy
   (chunk, embed, busca)   ├──> 02 SQL + RAG + recomendação
                           ├──> 03 SLM + automação
                           └──> 04 SLM + assistente de RH

00 ──> 05 GraphRAG ──┬──> 06 Agentic RAG sob medida ──> 07 Suporte + routing
                     └──> 08 Multimodal + LangGraph contábil
```

Você pode fazer 00 → 05 → 06 → 07 → 08, ou os módulos 01–04 em paralelo depois do 00.
O módulo 06 depende conceitualmente de 00 e 05; o 08 reutiliza 05 e 06.

## Trilha e investimento

| Módulo | Foco | Etapas | Tempo |
|---|---|---:|---:|
| `00_estudo_de_caso_rag_local` | Fundamentos: chunking, embeddings, retrieval, citação, abstenção | 5 | 2h00 |
| `01_projeto_llmops_deploy_rag` | API, ingestão idempotente, avaliação, observabilidade, Docker | 6 | 2h35 |
| `02_projeto_sql_llm_rag_recomendacao` | Schema linking, Text-to-SQL seguro, recomendação híbrida | 5 | 2h10 |
| `03_projeto_slm_rag_automacao` | SLM, intenção, SOPs, plano JSON, simulação | 5 | 2h00 |
| `04_projeto_slm_rag_assistente_rh` | Matching, evidências, anonimização, viés, entrevista | 6 | 2h30 |
| `05_projeto_graphrag_knowledge_graph` | Entidades, relações, multi-hop, híbrido, Neo4j | 6 | 2h50 |
| `06_projeto_agentic_rag_customizado` | Estado, router, ferramentas, reflexão, orçamento, trajetória | 6 | 2h30 |
| `07_projeto_agentic_rag_suporte_routing` | Triagem, prioridade, runbooks, aprovação, escalonamento | 6 | 2h30 |
| `08_projeto_multimodal_agentic_langgraph_contabil` | Imagem/PDF, extração, validação, RAG, revisão, auditoria | 6 | 2h50 |
| **Total** | | **51** | **~21h55** |

## Como estudar cada etapa

1. Abra o `README.md` do módulo e leia a linha da etapa no `PROGRESS.md`.
2. Leia o **conceito-âncora** e a **analogia**.
3. Abra o arquivo `src/` indicado; encontre o `TODO` e escreva o contrato em voz alta.
4. Implemente em 15–25 min. Rode a validação.
5. Se travar, consulte a escada de ajuda em `AGENTS.md`; só depois abra `solucao/`.
6. Compare a solução, explique a diferença e marque o checkbox.

**Regra de ouro:** nunca marque uma etapa sem saber explicar *por que* o resultado está correto.

## Estrutura

```text
curso-inteligencia-aumentada-rag/
├── AGENTS.md                  # contrato do tutor OpenCode
├── PROGRESS.md                # checklist de todas as micro-etapas
├── README.md
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── .env.example
├── Makefile
├── docs/ANALOGIAS.md
├── scripts/validate_repo.py
└── 0X_projeto_.../
    ├── README.md              # roteiro, analogia, arquitetura, dados
    ├── data/                  # corpus sintético
    ├── src/                   # esqueleto do aluno com TODO:
    ├── solucao/               # referência funcional
    └── tests/                 # smoke tests da referência
```

Cada `src/` contém tipagem, docstrings, contratos e marcadores `# TODO(etapa)`. Cada `solucao/`
é autocontida em Python padrão (quando possível) e inclui um `run_demo.py`.

## Convenções dos dados

- Datas, empresas, pessoas, CPFs/CNPJs, notas e valores são **fictícios**.
- Nenhum dataset deve ser usado para decisão real de crédito, RH, saúde ou contabilidade.
- Os arquivos de avaliação são pequenos e determinísticos para permitir testes rápidos.
- Dados “multimodais” incluem PNG/PDF sintéticos e um sidecar JSON com o texto esperado, simulando OCR.

## O que você saberá fazer ao final

- Projetar um pipeline RAG com chunking, índice, recuperação, citação e abstenção.
- Medir qualidade com um golden set e operar um serviço com logs e containers.
- Traduzir perguntas em SQL somente leitura, com schema linking e guardrails.
- Usar SLMs para classificação e automação com planos JSON validados.
- Fazer matching de RH com evidências, anonimização e auditoria de viés.
- Construir um grafo de conhecimento e responder perguntas multi-hop.
- Projetar agentes com router, ferramentas, orçamento, reflexão e aprovação humana.
- Orquestrar um fluxo multimodal contábil em LangGraph com trilha de auditoria.

## Solução de problemas

| Sintoma | Provável causa | Ação |
|---|---|---|
| `ModuleNotFoundError` em `src` | executou fora da pasta do módulo | `cd` no módulo e rode `python3 src/main.py` |
| demo da solução funciona, o seu não | `TODO` pendente | veja o `NotImplementedError` com o ID da etapa |
| FastAPI/LangGraph ausente | extra opcional não instalado | `pip install -r requirements.txt` |
| Docker não sobe Neo4j | porta ocupada ou senha curta | use `docker compose --profile graph up -d neo4j` |
| resposta RAG sem citação | threshold/retrieval fraco | valide com o golden set da etapa 0.5 |

## Ética

Este curso ensina sistemas de **aumento**, não substituição de julgamento humano. Aplicações de RH,
suporte e contabilidade usam dados sintéticos e incluem pontos explícitos de revisão humana. Em produção,
adicione governança, consentimento, avaliação contínua, observabilidade e conformidade com a LGPD.
