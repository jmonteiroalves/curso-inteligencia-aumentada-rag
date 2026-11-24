# PROGRESS — trilha de 51 micro-etapas

Marque `[x]` **somente** depois de rodar a validação e explicar o resultado.
Tempo total estimado: **~21h55**. Faça uma etapa por bloco; pare no critério de validação.

Legenda: `⏱` tempo-alvo · `🎯` evidência mínima · `📁` arquivo de trabalho.
Cada módulo tem `README.md` com conceito, analogia e dicas. Soluções em `solucao/`.

## 00 — Estudo de caso RAG local (2h00)

- [ ] **0.1 Inventário e chunking** ⏱20 · 📁 `src/rag.py` · 🎯 chunk de 450 chars com overlap, sem cortar palavras
- [ ] **0.2 Embeddings determinísticos e índice** ⏱25 · 📁 `src/rag.py` · 🎯 vetores normalizados e índice consultável
- [ ] **0.3 Busca top-k e similaridade** ⏱20 · 📁 `src/rag.py` · 🎯 top-3 contém a fonte esperada para 5 perguntas
- [ ] **0.4 Prompt aterrado, citação e abstenção** ⏱25 · 📁 `src/rag.py` · 🎯 toda resposta cita fonte; pergunta fora do corpus abstém
- [ ] **0.5 Avaliação com golden set** ⏱30 · 📁 `solucao/evaluate.py` · 🎯 relatório com hit@3 e taxa de abstenção

## 01 — LLMOps e deploy de RAG (2h35)

- [ ] **1.1 Contrato da API e healthcheck** ⏱20 · 📁 `src/app.py` · 🎯 `GET /health` e modelos Pydantic definidos
- [ ] **1.2 Ingestão idempotente + chunks** ⏱30 · 📁 `src/rag_core.py` · 🎯 reingestão não duplica documentos
- [ ] **1.3 Endpoint de consulta e citações** ⏱30 · 📁 `src/app.py` · 🎯 `POST /query` retorna resposta, fontes e latência
- [ ] **1.4 Golden set e avaliação offline** ⏱25 · 📁 `solucao/evaluate.py` · 🎯 hit@3 ≥ 0,8 no dataset local
- [ ] **1.5 Observabilidade e logs estruturados** ⏱20 · 📁 `src/rag_core.py` · 🎯 log JSON com request_id, top_k e score
- [ ] **1.6 Empacotamento Docker e configuração** ⏱30 · 📁 `Dockerfile` · 🎯 imagem builda e healthcheck responde

## 02 — SQL + LLM + RAG + recomendação (2h10)

- [ ] **2.1 Modelo relacional e schema** ⏱25 · 📁 `data/loja.db` · 🎯 consultas de conferência retornam contagens esperadas
- [ ] **2.2 Recuperação de schema** ⏱20 · 📁 `src/sql_rag.py` · 🎯 pergunta de produto seleciona tabelas relevantes
- [ ] **2.3 Text-to-SQL com guardrails** ⏱30 · 📁 `src/sql_rag.py` · 🎯 rejeita DROP/DELETE, múltiplos statements e tabelas desconhecidas
- [ ] **2.4 Execução segura e resposta** ⏱25 · 📁 `src/sql_rag.py` · 🎯 consulta somente leitura com `LIMIT` e explicação
- [ ] **2.5 Recomendação híbrida e avaliação** ⏱30 · 📁 `src/sql_rag.py` · 🎯 top-3 inclui item co-comprado; precision@3 registrada

## 03 — SLM + RAG + automação (2h00)

- [ ] **3.1 Catálogo de intenções e SOPs** ⏱20 · 📁 `data/sops/` · 🎯 4 intenções e 4 SOPs mapeados
- [ ] **3.2 Classificador SLM com fallback** ⏱25 · 📁 `src/automation.py` · 🎯 8 solicitações classificadas; incerteza escala
- [ ] **3.3 Retrieval de procedimento** ⏱20 · 📁 `src/automation.py` · 🎯 SOP correto no top-1 para casos rotulados
- [ ] **3.4 Plano de ação JSON validado** ⏱25 · 📁 `src/automation.py` · 🎯 plano rejeita ação/tool inexistente e campo faltante
- [ ] **3.5 Simulador de automação e métricas** ⏱30 · 📁 `src/automation.py` · 🎯 execução simulada produz taxa de sucesso e escalonamentos

## 04 — SLM + RAG + assistente de RH (2h30)

- [ ] **4.1 Dados de RH e anonimização** ⏱25 · 📁 `src/rh_rag.py` · 🎯 nome/e-mail/telefone removidos antes do matching
- [ ] **4.2 Perfil da vaga e critérios** ⏱20 · 📁 `src/rh_rag.py` · 🎯 critérios com pesos somam 1,0 e são justificáveis
- [ ] **4.3 Matching currículo-vaga** ⏱30 · 📁 `src/rh_rag.py` · 🎯 ranking determinístico com score 0–100
- [ ] **4.4 Evidências e explicabilidade** ⏱25 · 📁 `src/rh_rag.py` · 🎯 cada ponto do score aponta trecho do currículo
- [ ] **4.5 Entrevista estruturada** ⏱20 · 📁 `src/rh_rag.py` · 🎯 5 perguntas ligadas a critérios, sem perguntas protegidas
- [ ] **4.6 Auditoria de viés e relatório** ⏱30 · 📁 `solucao/evaluate.py` · 🎯 relatório de taxa de seleção por grupo sintético

## 05 — GraphRAG e knowledge graph (2h50)

- [ ] **5.1 Extração de entidades** ⏱25 · 📁 `src/graph_rag.py` · 🎯 entidades tipadas sem duplicatas no corpus
- [ ] **5.2 Extração de relações e schema** ⏱30 · 📁 `src/graph_rag.py` · 🎯 triplas válidas com sujeito-predicado-objeto
- [ ] **5.3 Construção do grafo** ⏱25 · 📁 `src/graph_rag.py` · 🎯 vizinhos e grau conferem com inspeção manual
- [ ] **5.4 Consultas multi-hop** ⏱30 · 📁 `src/graph_rag.py` · 🎯 caminho de 2–3 saltos responde pergunta relacional
- [ ] **5.5 GraphRAG híbrido** ⏱30 · 📁 `src/graph_rag.py` · 🎯 contexto combina chunks + subgrafo e cita evidências
- [ ] **5.6 Exportação Neo4j e comunidades** ⏱30 · 📁 `solucao/neo4j_export.py` · 🎯 Cypher idempotente + sumário de comunidade

## 06 — Agentic RAG customizado (2h30)

- [ ] **6.1 Estado do agente e contrato** ⏱20 · 📁 `src/agent.py` · 🎯 estado serializável com pergunta, passos e evidências
- [ ] **6.2 Router de decisão** ⏱25 · 📁 `src/agent.py` · 🎯 roteia retrieval, cálculo ou resposta direta
- [ ] **6.3 Ferramenta de retrieval** ⏱20 · 📁 `src/agent.py` · 🎯 ferramenta retorna trechos citáveis ou vazio
- [ ] **6.4 Ferramenta calculadora/checklist** ⏱25 · 📁 `src/agent.py` · 🎯 cálculo exato sem eval de expressão arbitrária
- [ ] **6.5 Loop de reflexão e orçamento** ⏱30 · 📁 `src/agent.py` · 🎯 máximo de passos; loop encerra com fallback
- [ ] **6.6 Avaliação de trajetória** ⏱30 · 📁 `solucao/evaluate.py` · 🎯 acurácia final + ferramentas corretas + passos médios

## 07 — Agentic RAG para suporte e routing (2h30)

- [ ] **7.1 Taxonomia de tickets** ⏱20 · 📁 `data/tickets.jsonl` · 🎯 10 tickets rotulados em 4 domínios
- [ ] **7.2 Router de fila e prioridade** ⏱25 · 📁 `src/support_agent.py` · 🎯 P1 crítico roteado em ≤1 passo com justificativa
- [ ] **7.3 Runbooks como ferramentas** ⏱25 · 📁 `src/support_agent.py` · 🎯 runbook correto recuperado por domínio
- [ ] **7.4 Ações com aprovação humana** ⏱30 · 📁 `src/support_agent.py` · 🎯 reembolso nunca executa sem aprovação
- [ ] **7.5 Política de escalonamento** ⏱20 · 📁 `src/support_agent.py` · 🎯 3 gatilhos de handoff documentados e testados
- [ ] **7.6 Simulador e métricas operacionais** ⏱30 · 📁 `solucao/evaluate.py` · 🎯 contenção, handoff e SLA risk medidos

## 08 — Multimodal + Agentic + LangGraph contábil (2h50)

- [ ] **8.1 Ingestão multimodal** ⏱25 · 📁 `src/accounting_agent.py` · 🎯 imagens/PDFs indexados com fonte e checksum
- [ ] **8.2 Extração de nota fiscal** ⏱30 · 📁 `src/accounting_agent.py` · 🎯 número, CNPJ, itens e totais extraídos
- [ ] **8.3 Normalização e validação contábil** ⏱30 · 📁 `src/accounting_agent.py` · 🎯 soma dos itens = total; divergência bloqueia
- [ ] **8.4 RAG sobre demonstrativos** ⏱25 · 📁 `src/accounting_agent.py` · 🎯 consulta responde com linha e fonte
- [ ] **8.5 Grafo LangGraph com revisão** ⏱30 · 📁 `solucao/langgraph_flow.py` · 🎯 fluxo ingest→extract→validate→review→report
- [ ] **8.6 Relatório e trilha de auditoria** ⏱30 · 📁 `src/accounting_agent.py` · 🎯 relatório reproduzível com decisões e evidências

---

## Registro de sessões

Use este bloco para anotar bloqueios e decisões (uma linha por sessão).

| Data | Etapa | O que funcionou | Bloqueio / decisão |
|---|---|---|---|
| | | | |
