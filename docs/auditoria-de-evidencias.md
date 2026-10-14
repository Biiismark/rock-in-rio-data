# Auditoria de evidências e rastreabilidade

Este registro liga afirmações sobre o projeto aos artefatos que as sustentam. Os relatórios completos de origem permanecem no Drive de trabalho; esta página é a síntese pública. Por isso, a publicação não substitui a disponibilização controlada dos registros primários a pareceristas quando a revista solicitar.

## Linha temporal documentada

| Data do registro | O que o relatório comprova | Uso no relato tecnológico |
|---|---|---|
| 03/09/2026 — Auditoria Geral das Bases, Fase 1 | A auditoria identificou 26–27/08 ausentes no histórico Spotify então disponível, HTTP 429 nas consultas relacionadas do Trends em 28/08 e classificação prevista incorretamente para 08–10/09 na função de fase. A série principal Trends executou oito lotes. | Evidência de falhas reais encontradas antes da consolidação; não tratar como intenção de protocolo. |
| 09/09/2026 — Relatório Científico Diário | Registra reconstrução Trends V2 com 30 entidades, 7.544 observações de interesse 2026, 1.537 de baseline, 810 regionais e 604 registros de consultas relacionadas nessa saída diária. Também registra a inclusão prospectiva de eventos Analytics: `section_view`, `external_link_click`, `artist_open` e `news_detail_open`. | Evidência de evolução do artefato e instrumentação; a execução diária é um estado histórico, não o estado atual do banco. |
| 16/09/2026 — Relatório Científico Diário | Trends tinha 7.710 observações consolidadas e 60 provisórias; consolidação permitiu verificar checkpoints D+3/D+1 de grupos específicos. | Demonstra maturação progressiva e regra de não promover provisórios prematuramente. |
| 20/09/2026 — Relatório Científico Diário | Trends tinha 7.830 consolidadas; 19 e 20/09 permaneciam provisórias; D+7 do último dia ainda não podia ser fechado. | Evidência de que o marco cronológico não foi confundido com maturidade dos dados. |
| 26/09/2026 — Auditoria pós-automação | Relata execução #39 bem-sucedida, 73/73 arquivos e 28/28 snapshots sincronizados sem erro naquele teste. | Evidência de uma reconciliação operacional delimitada. |
| 28/09/2026 — Relatório Final de Auditoria e Congelamento | Define corte 16:32:48 BRT; 28 artistas, 7 datas, 4 apresentações/dia; 8.040 linhas/30 entidades Trends; 7.980 consolidadas e 60 provisórias; baseline 1.537/29; 112/112 checkpoints; Spotify 5.800 até 25/09; Charts 24 métricas; TikTok 2.592/1.150/621; Heineken 117; Actions #40 com sucesso. | Âncora para todos os resultados primários. |
| 13/10/2026 — Acompanhamento Complementar D+30 | Esclarece que D+30 é apenas marco cronológico: Trends até 25/09, Spotify até 11/10 (D+28), charts/TikTok até 12/10 (D+29), Heineken até 09/10; sem Trends em D+30. | Evidência complementar pós-freeze, mantida separada da base primária. |
| 14/10/2026 — consulta de metadados e contagens Supabase | Trends: 8.040 linhas, 30 entidades e 60 parciais; baseline: 1.537/29; related queries: tabela vazia; TikTok: 4.128 KWORB, 1.847 rankings e 1.729 histórico até 13/10. | Estado operacional posterior, usado para verificar persistência e crescimento pós-freeze. |

## Divergências e pendências que afetam a interpretação

| Questão | Evidência de origem | Evidência atual | Situação |
|---|---|---|---|
| Consultas relacionadas Trends | Relatório diário de 09/09 declara 604 registros nessa saída. | `public.trends_v2_consultas` estava com 0 linhas em leitura de 14/10; congelamento não estabelece uma reconciliação dos 604. | Divergência de persistência aberta; não dizer simplesmente que nunca foram coletadas nem afirmar recuperação definitiva. |
| Spotify 26–27/08 | Auditoria de 03/09 indica ausência de linhas e falta de backfill automático naquele momento. | 5.800 linhas no freeze, mas o total agregado não informa se essas duas datas foram recuperadas. | Backfill não comprovado sem teste de calendário na versão congelada. |
| Fase 08–10/09 | Auditoria de 03/09 identifica regra incorreta; script corretivo e workflow foram confirmados no código posterior. | Ainda não foi anexado diff/contagem de linhas do snapshot científico. | Correção operacional confirmada; impacto histórico quantificado não confirmado. |
| Analytics do site | Em 08/09 não havia série validada; instrumentação implantada prospectivamente em 09/09. | O material consultado não apresenta série de uso validada no freeze. | Não retroestimar acessos nem alegar avaliação de usabilidade. |
| D+30 | Relatório de 13/10 informa últimos dados anteriores ao marco em várias fontes. | Nenhuma cobertura integral das fontes em 13/10; Trends termina em D+21 relativo. | Chamar de checkpoint D+30 complementar, não de coleta completa D+30. |
| Dados e reprodução pública | Código e documentação publicados. | O conjunto de dados congelado e snapshots não estão incluídos neste repositório. | O pacote atual permite avaliar documentação/código e resultados resumidos; não reproduzir integralmente os resultados sem acesso aos dados. |

## Materiais consultados

- `Auditoria_Geral_Bases_Rock_in_Rio_2026_Fase_1` — 03/09/2026.
- `Relatorio_Cientifico_Diario_Rock_in_Rio_2026` — entradas de 09, 16 e 20/09/2026.
- `Auditoria_Pos_Automacao_Rock_in_Rio_2026` — 26/09/2026.
- `Relatorio_Final_Auditoria_Congelamento_Rock_in_Rio_2026` — 28/09/2026.
- `Acompanhamento_Complementar_D30_Rock_in_Rio_2026` — 13/10/2026.
- Supabase `rock-in-rio-2026`, tabelas públicas consultadas em leitura somente de metadados/contagens — 14/10/2026.

Os registros originais são documentos de trabalho no Drive do autor e não estão vinculados publicamente. A versão pública deste dossiê contém as sínteses e as lacunas identificadas; o autor deve conservar os arquivos de origem e fornecer acesso ao parecerista se solicitado e permitido.