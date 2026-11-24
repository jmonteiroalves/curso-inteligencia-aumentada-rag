# Manutenção preditiva de compressores

O programa de manutenção preditiva monitora compressores industriais por meio de sensores de
vibração e temperatura. A leitura de vibração é coletada a cada 10 minutos pelo gateway e enviada
para o pipeline de análise. Um alerta preventivo é aberto quando a vibração RMS ultrapassa
7,5 mm/s por três leituras consecutivas.

O modelo de classificação usado em produção é um Random Forest treinado com 18 meses de histórico.
Na validação mais recente, ele alcançou precisão de 0,89 e recall de 0,82 para falha em 72 horas.
Falsos positivos geram inspeção visual; falsos negativos são tratados como prioridade máxima de
melhoria do modelo.

A inspeção presencial deve ocorrer em até 24 horas após um alerta preventivo. Se houver também
temperatura acima de 95 °C, a recomendação é reduzir a carga para 60% e acionar o time de
confiabilidade imediatamente. O histórico de cada ativo fica no sistema de gestão de manutenção.
