# Arquitetura edge da linha de produção

Cada linha possui um gateway industrial que fala MQTT com os sensores e mantém um buffer local
de 72 horas. Quando a conexão com a nuvem cai, o gateway continua coletando e sincroniza os dados
em lote ao reconectar. O buffer é criptografado em repouso e usa uma chave rotacionada a cada 90 dias.

O processamento sensível à latência ocorre na borda: detecção de anomalia simples e parada de
emergência. A nuvem executa treinamento de modelos, consolidação de indicadores e APIs de consulta.
A comunicação usa TLS mútuo; cada gateway tem um certificado emitido pela PKI interna.

O deploy de firmware é feito em ondas de 5% dos dispositivos, com rollback automático se a taxa de
erro de telemetria passar de 2%. Não há atualização automática em horário de produção crítica.
