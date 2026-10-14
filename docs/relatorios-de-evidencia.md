# Registro de relatórios, resultados e limites de evidência

Este documento resume os registros de coleta e auditoria produzidos durante o projeto. Os relatórios originais permanecem no Drive do projeto; esta síntese pública não os substitui. Datas de produção do relatório e datas de referência dos dados são mantidas distintas.

## Registros consultados

| Registro | Evidência documentada | Uso e limite |
|---|---|---|
| Auditoria geral da base, 03/09/2026 | Universo configurado com 28 artistas em sete datas. A auditoria registrou ausência de dados Spotify de 26–27/08 no snapshot então disponível e erro HTTP 429 em consultas relacionadas do Google Trends em 28/08. Também apontou classificação incorreta das datas 08–10/09 na fase do monitoramento. | Evidência de lacunas e incidentes naquele estado da base. Não prova que os dias Spotify ausentes foram recuperados depois. |
| Relatório diário de 09/09/2026 | Relata V2 com 30 entidades, 7.544 linhas de interesse de 2026, 1.537 linhas de baseline, 810 linhas regionais e 604 registros de consultas relacionadas. Registra que a instrumentação de Analytics foi iniciada prospectivamente em 09/09, com eventos como visualização de seção, clique externo, abertura de artista e detalhe de notícia. | Evidência de resultados comunicados naquele dia; os totais são um retrato datado, não totais finais. Analytics não permite reconstruir uso anterior à instrumentação. |
| Relatório diário de 16/09/2026 | Registra 7.710 observações consolidadas de Trends e 60 provisórias, com maturação D+3 e D+1. | Reforça que o estado recente era provisório e que a data de coleta/relatório não equivale à data consolidada. |
| Relatório diário de 20/09/2026 | Registra 7.830 observações consolidadas, com 19 e 20/09 ainda provisórias; nem todos os pontos D+7 estavam maduros. | O número é o estado naquele relatório, anterior ao congelamento final. |
| Auditoria pós-festival, 26/09/2026 | Registra execução bem-sucedida da Action #39, sincronização de 73/73 arquivos e 28/28 snapshots sem erro. Os totais descritos no relatório são daquele estado operacional. | Evidência de execução/sincronização, não de validade substantiva de todos os indicadores. |
| Relatório final de auditoria e congelamento, 28/09/2026, 16:32:48 BRT | Define RIR2026_FREEZE_1.0. Registra 8.040 linhas de Trends V2 para 30 entidades, sendo 7.980 consolidadas até 23/09 e 60 provisórias de 24–25/09; baseline de 1.537 linhas/29 entidades com Nova Twins N/D; checkpoints D0/D+1/D+3/D+7: 112/112 consolidados; Spotify: 5.800 linhas até 25/09; 24 métricas de charts até 27/09; TikTok: 2.592 KWORB, 1.150 rankings, 621 históricos e 0/28 artistas nas listas monitoradas; Heineken: 117 publicações até 16/09. A integridade foi marcada OK. | É o corte científico de referência. “Integridade OK” e execução bem-sucedida descrevem verificações operacionais registradas, não validação externa de cada fonte nem prova de causalidade. |
| Acompanhamento complementar D+30, 13/10/2026 | No relatório, Trends chegava a 25/09 (consolidado até 23/09; maior distância relativa D+21), Spotify a 11/10 (D+28), charts e TikTok a 12/10 (D+29) e Heineken a 09/10. | O rótulo D+30 não representa um corte completo D+30. É acompanhamento posterior e não altera o freeze. |

## Falhas, correções e pendências verificáveis

### Consultas relacionadas do Google Trends

Há três fatos distintos que precisam permanecer separados:

1. A auditoria de 03/09 registra erro HTTP 429 em consultas relacionadas ocorrido em 28/08.
2. O relatório diário de 09/09 relata 604 registros de consultas relacionadas na saída daquele dia.
3. Na inspeção do Supabase em 14/10/2026, a tabela `trends_v2_consultas` continha zero linhas.

A divergência entre a saída histórica relatada e a persistência atual não foi reconciliada. Não é correto afirmar que a coleta nunca ocorreu, que os 604 registros foram recuperados com sucesso ou que o problema está resolvido. O inventário público registra ambos os estados.

### Aumento do intervalo entre chamadas e retentativa

A rotina V2 usa intervalo aleatório de 65–85 segundos entre chamadas e espera de 300 segundos antes de uma retentativa após HTTP 429, segundo os parâmetros registrados no código e nos relatórios consultados. Isso aumenta o tempo de extração. Não foi localizada comparação controlada que estime quanto a mudança reduziu a taxa de erro; portanto, descrevê-la como resposta implementada é sustentado, e afirmar eficácia quantificada não é.

### Lacuna Spotify de 26–27/08

A auditoria de 03/09 documenta a ausência desses dias no snapshot analisado naquele momento. O freeze posterior relata 5.800 linhas até 25/09, mas o total agregado não prova que os dias foram preenchidos. A recuperação permanece sem comprovação linha a linha na evidência consultada.

### Classificação das fases

A auditoria de 03/09 aponta classificação incorreta de 08–10/09. O repositório contém uma rotina de correção de fase referenciada no workflow. A documentação disponível confirma a existência da correção; não foi obtida uma comparação quantificada do snapshot antes/depois para afirmar quantas linhas foram alteradas.

### Uso da interface

Os relatórios dizem que Analytics foi instrumentado prospectivamente em 09/09. Não há série de uso retroativa validada nos registros do freeze. Uma observação isolada de carregamento/spinner não é medida de disponibilidade contínua nem de desempenho.

## O que o artigo ferramental pode afirmar

Os registros sustentam a descrição do observatório implementado, das fontes integradas, das rotinas automatizadas, dos controles de estado e maturação, dos incidentes observados, das respostas de código e das contagens do corte congelado. Eles não sustentam inferência causal de impacto do festival nos artistas, eficácia estatística do backoff, recuperação confirmada da lacuna Spotify ou validação de usabilidade da interface.

O corte de dados está acessível no repositório operacional fixado em `f508aaa78631ecddbedcb4bd117c0b1041b2c17c`, com manifesto dos arquivos neste dossiê. Os relatórios originais permanecem no Drive. O acesso aos dados está resolvido; ainda não foi feita reprodução independente, comando a comando, de todos os totais do artigo.

## Referência deste registro

Observatório Rock in Rio. (2026). *Registro de relatórios, resultados e limites de evidência* [Síntese pública de registros técnicos]. GitHub. https://github.com/Biiismark/rock-in-rio-data/blob/main/docs/relatorios-de-evidencia.md
