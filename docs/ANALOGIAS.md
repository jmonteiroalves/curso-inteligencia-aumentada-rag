# Analogias-âncora

Use uma analogia por conceito, não cinco. Elas servem para criar um modelo mental; a validação vem do código.

| Conceito | Analogia | O que a analogia ensina | Onde ela quebra |
|---|---|---|---|
| LLM sem RAG | Palestrante brilhante sem os arquivos da empresa | fluência não é conhecimento atualizado | o LLM pode ter memorizado parte do corpus |
| RAG | Bibliotecário que busca fichas antes de responder | recuperar → aumentar → gerar | o bibliotecário pode pegar a ficha errada |
| Chunking | Recortar um livro em fichas de estudo | granularidade afeta precisão e contexto | fichas perdem relações entre capítulos |
| Embedding | Mapa de proximidade semântica | textos parecidos ficam perto | proximidade não é verdade nem atualidade |
| Busca top-k | Pescar os k peixes mais próximos da isca | recall × precisão | o peixe certo pode estar fora do lago |
| Reranking | Revisor que relê os finalistas | precisão barata depois do recall | aumenta latência e custo |
| Citação | Nota de rodapé verificável | auditabilidade e confiança | uma citação correta não garante inferência correta |
| Abstenção | “Não sei” do profissional responsável | reduz alucinação | abster demais destrói utilidade |
| GraphRAG | Mapa de metrô em vez de lista de estações | relações e multi-hop | extração de arestas erradas contamina o grafo |
| Comunidade de grafo | Bairros e suas conexões | sumarização global | comunidades pequenas podem ser ruído |
| Agente | Gerente com ferramentas e orçamento | decide, age, observa e revisa | sem limites, entra em loop |
| Router | Recepcionista que encaminha o chamado | escolha de caminho | taxonomia incompleta gera fila errada |
| Ferramenta | Calculadora, busca, CRM | precisão fora do LLM | ferramenta sem permissão vira risco |
| Aprovação humana | Assinatura antes do saque | controle de ação irreversível | aprovação em massa vira carimbo |
| LangGraph | Fluxograma executável com estado | ciclos, branches e retomada | grafo complexo é difícil de depurar |
| Avaliação RAG | Prova com gabarito e prova em branco | mede recall, groundedness e abstenção | golden set pequeno não representa produção |
| LLMOps | Cozinha industrial com rastreabilidade | deploy, versão, logs, rollback | processo pesado demais mata iteração |
| Viés em RH | Régua que mede sempre o mesmo lado | decisão precisa ser auditável | remover o atributo não remove o viés histórico |
| Multimodal | Mesa de auditoria com papel, imagem e planilha | cruzar evidências | OCR erra e visão alucina números |

## Frases de bolso

- **“Recuperar antes de gerar.”**
- **“Sem citação, é opinião.”**
- **“Grafo é para relações; vetor é para semelhança.”**
- **“Agente é um loop com orçamento, não um chatbot com superpoderes.”**
- **“Toda ação irreversível precisa de um humano no circuito.”**
- **“Se você não mede, você só tem uma demo.”**
