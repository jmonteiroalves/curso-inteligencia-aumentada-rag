# Aurora Flow — visão do produto

O Aurora Flow é uma plataforma fictícia de automação de processos para equipes financeiras.
Ela possui três módulos: Captura (ingestão de documentos), Conciliação (comparação de lançamentos)
e Painéis (indicadores em tempo real). Os módulos podem ser contratados separadamente.

A Captura aceita PDF, PNG e XML e usa OCR para extrair campos. A Conciliação compara o extrato
bancário com o razão contábil e sinaliza divergências acima de R$ 50,00. Os Painéis atualizam a
cada 5 minutos e permitem exportar CSV e XLSX.

O produto foi desenhado para escritórios de contabilidade com 5 a 200 colaboradores. A retenção
padrão de documentos é de 5 anos, configurável por contrato. Toda exportação é registrada em log
de auditoria com usuário, data, hora e filtros aplicados.
