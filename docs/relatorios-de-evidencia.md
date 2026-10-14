# Relatórios de auditoria e trilha de evidência

Este arquivo consolida evidências técnicas dos relatórios diários e de fechamento consultados. É um resumo de projeto preparado para avaliação pública; não republica o arquivo bruto de cada relatório ou dados de plataforma. Horário do relatório e data efetiva dos dados são mantidos separados.

## Linha de corte e evidência de coleta

| Registro | Produzido/coletado | Evidência resumida |
|---|---|---|
| Protocolo pré-evento / auditoria de base | 03/09/2026 | Universo configurado: 28 artistas, sete datas, quatro apresentações/dia. Foram identificadas a falha HTTP 429 na coleta de consultas relacionadas em 28/08 e a lacuna Spotify para 26–27/08 no snapshot então disponível. |
| Relatórios diários do primeiro fim de semana | 04–10/09/2026 | Relatórios registram frescor distinto por fonte. Em 08/09, o Spotify tinha referência em 06/09; não se retroestimaram acessos do site onde Analytics não estava comprovado. Em 09/09 foi iniciada instrumentação prospectiva de uso. A camada Trends legada foi marcada provisória durante a migração V2. |
| Nota operacional Google Trends V2 | 10/09/2026 | V2 consulta cada entidade individualmente, usa Topic/MID validado, interpreta escala dentro da entidade, mantém até dois dias recentes provisórios e guarda status/metadata. Consultas relacionadas aparecem como N/D quando endpoint/quota não permite recuperação. |
| Auditoria pós-festival | 26/09/2026 | GitHub Actions #39 concluída com sucesso; status de integridade reportado para 28 artistas, 29 métricas de charts, 5.600 linhas Spotify, 28 entidades de lineup monitoradas em TikTok, 117 itens editoriais Heineken e 7.980 observações Trends consolidadas. O relatório registra sincronização 73/73 arquivos e 28/28 snapshots, sem erro. |
| Freeze científico | 28/09/2026, corte às 16:32:48 BRT | Versão RIR2026_FREEZE_1.0. A execução Actions #40 terminou em 27/09. Trends: 8.040 linhas/30 entidades; 7.980 consolidadas até 23/09 e 60 provisórias de 24–25/09; 1.537 linhas de baseline em 29 entidades; Nova Twins N/D. Checkpoints D0/D+1/D+3/D+7: 112/112 consolidados. Spotify: 5.800 linhas até 25/09. Charts com referência até 27/09. |
| Checkpoint complementar D+30 | 13/10/2026 | Relatório gerado em 13/10, mas nem todas as fontes tinham dado de 13/10: charts/TikTok até 12/10 (D+29), Spotify até 11/10 (D+28), Heineken até 09/10 e Trends até 25/09, consolidado até 23/09. Para Trends, maior D relativo disponível era D+21. Portanto, o relatório não comprova uma observação integral D+30. O corte principal de 28/09 permanece imutável. |

## Achados extraídos dos relatórios diários

1. **Limitação operacional do Trends relacionado:** erro 429 documentado para a rotina de consultas relacionadas. A série de interesse primária é uma saída distinta. Ausência no endpoint related topics não foi convertida em zero.
2. **Resposta técnica a quota:** na implementação V2, o intervalo de chamada aumentou para 65–85 segundos (aleatório) e a rotina espera 300 segundos antes de uma retentativa após erro 429. Essa política torna a execução mais lenta. Os relatórios/code review confirmam os parâmetros; não foi encontrado experimento que compare taxa de erro pré e pós-mudança.
3. **Qualidade temporal:** relatórios diários mostram que a última data disponível muda por fonte. Usar dia do relatório como se fosse data observada gera desfasagem; os três tempos devem permanecer separados.
4. **Spotify:** a auditoria em 03/09 documenta lacuna 26–27/08 e ausência de backfill automático. Os totais cumulativos de 5.800 linhas do freeze não são evidência suficiente para provar recuperação. Requer inspeção linha a linha.
5. **Fase do monitoramento:** o código público de correção recalcula fases do diário e define 08–10/09 como intervalo entre os fins de semana. A rotina está referenciada no workflow. Para comprovar aplicação no snapshot de pesquisa, ainda é necessário anexar diff/contagem de linhas alteradas.
6. **Analytics da interface:** um relatório de 08/09 registra que não havia dados confiáveis de uso; a instrumentação passou a ser prospectiva em 09/09. Não estimar acessos retroativamente.
7. **Integridade de versões:** o congelamento científico está separado da operação posterior. Dados novos, mudança tardia e inclusão retrospectiva devem ser adendos versionados.

## Interpretação para o manuscrito ferramental

A evidência sustenta completude dos checkpoints, existência de automação e tratamento explícito de status/provisório; ela não sustenta causalidade sobre repercussão musical, eficácia quantitativa do backoff, recuperação automática da lacuna Spotify ou usabilidade do site. O artigo deve apresentar os resultados acima como medidas de cobertura e funcionamento do artefato.

## Referência bibliográfica ao registro público

Observatório Rock in Rio. (2026). *Relatórios de auditoria e trilha de evidência: Rock in Rio 2026* [Resumo público de registros técnicos]. GitHub. https://github.com/Biiismark/rock-in-rio-data/blob/main/docs/relatorios-de-evidencia.md
