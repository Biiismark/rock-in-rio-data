# Resultados e avaliação do artefato

## Artefato colocado em operação

O projeto implementou um observatório digital para monitorar fontes públicas relacionadas aos artistas do Palco Mundo. A unidade de configuração foi um conjunto de 28 artistas distribuídos em sete datas. O artefato integrou scripts Python, workflows GitHub Actions, tabelas e arquivos no Supabase, arquivos versionados e uma interface web.

A operação manteve fontes separadas por unidade e data efetiva. O registro de execução não substituiu a data de referência publicada pela fonte. Nas rotinas e relatórios, valores provisórios, falhas de consulta, não detecção em listas e N/D ficaram distintos de zero observado.

## Cobertura observada no congelamento de 28/09/2026

| Fonte/resultado | Valor registrado | Limite do que o valor demonstra |
|---|---:|---|
| Universo do Palco Mundo | 28 artistas; 7 dias | Integridade estrutural do recorte configurado. |
| Google Trends V2 | 8.040 linhas; 30 entidades | Volume de observações do sistema, não buscas absolutas. |
| Trends consolidados | 7.980 até 23/09 | Séries consideradas maduras até a data declarada. |
| Trends provisórios | 60, de 24–25/09 | Permanecem fora das conclusões consolidadas. |
| Baseline Trends 2025 | 1.537 linhas; 29 entidades | Uma entidade, Nova Twins, não tem baseline válido e continua N/D. |
| Checkpoints Trends | 112/112 consolidados em D0, D+1, D+3 e D+7 | Completude dos marcos previstos; não identifica causalidade. |
| Spotify diário | 5.800 linhas até 25/09 | Cobertura do ranking observado; não mede toda atividade de streaming. |
| Charts | 24 métricas até referência 27/09 | Presença em listas distintas; não equivale a volume de consumo. |
| TikTok KWORB / rankings / histórico | 2.592 / 1.150 / 621 linhas no relatório de congelamento | Linhas de fontes e granularidades diferentes não são alcance somável. |
| TikTok — artistas do lineup | 0/28 detectados nas listas monitoradas | Não detecção nessas listas, não zero de uso na plataforma. |
| Heineken editorial | 117 publicações; última publicação em 16/09 | Corpus editorial auxiliar, não resultado sobre efeito do evento. |
| GitHub Actions | Run #40 concluído com sucesso em 27/09 | Evidência de uma execução bem-sucedida; não prova sucesso de todas as execuções anteriores. |

## Avaliação técnica que os registros permitem

Os relatórios do freeze registram os testes de integridade como OK para programação, presença, charts, Spotify, TikTok, Heineken e Trends V2. A execução #40 é indicada como sucesso. A auditoria pós-automação de 26/09 registrou sincronização de 73/73 arquivos e 28/28 snapshots sem erro. Esses resultados apoiam completude estrutural e integridade dos objetos verificados naquele corte.

A evidência não inclui teste formal com usuários, série validada de disponibilidade do site, tempos de resposta, cobertura de Analytics suficiente para avaliação de uso nem teste independente de reprodução do pacote congelado. Uma observação do site em estado de carregamento foi registrada uma vez; ela não demonstra indisponibilidade contínua.

## Estado observado em auditoria do Supabase em 14/10/2026

A leitura administrativa somente de metadados/contagens encontrou:

| Tabela | Linhas | Datas efetivas / entidades |
|---|---:|---|
| `trends_v2_interesse` | 8.040 | 2026-01-01 a 2026-09-25; 30 entidades; 60 `is_partial=true` |
| `trends_v2_baseline_2025` | 1.537 | 2024-12-29 a 2025-12-28; 29 entidades |
| `trends_v2_entidades` | 30 | 30 IDs de artista/entidade |
| `trends_v2_consultas` | 0 | Sem linhas persistidas na tabela consultada |
| `trends_v2_regioes` | 789 | Validação indicada entre 08 e 18/09; 30 entidades |
| `tiktok_kworb` | 4.128 | 01/09 a 13/10/2026 |
| `tiktok_rankings` | 1.847 | 27/08 a 13/10/2026 |
| `tiktok_historico` | 1.729 | 28/07 a 13/10/2026 |

Essas contagens são estado operacional consultado em 14/10 e não substituem o freeze. As contagens TikTok são maiores que as do corte científico porque receberam atualização posterior. A tabela `trends_v2_consultas` vazia não apaga o registro diário de 09/09 que informou 604 registros de consultas relacionadas: indica uma divergência entre uma saída reportada à época e a persistência atual no banco, ainda sem reconciliação.

## Evidência complementar D+30 — 13/10/2026

O relatório complementar de 13/10 delimitou o próprio alcance: Trends tinha dados até 25/09, consolidados até 23/09, sem observações de busca em D+30; Spotify chegava a 11/10 (D+28); charts e TikTok a 12/10 (D+29); Heineken a 09/10. O maior D relativo do Trends era D+21.

Na comparação de charts feita no relatório complementar, seis fontes comuns registraram 24 itens em 03/09, 19 em 20/09 e 15 em 12/10. O relatório interpreta a queda como redução de itens detectados no recorte comparável, não como queda equivalente de audiência ou consumo. Spotify detectou Pedro Sampaio nos cortes 20/09 e 11/10; os demais não aparecem no Top 200 observado. TikTok não detectou artistas do lineup nas duas listas monitoradas em 28/09 nem em 12/10.

## Resultado e limite da avaliação

O projeto demonstrou um sistema operado com rotina de coleta, validação, armazenamento e documentação, além de 112 checkpoints principais de Trends consolidados. Também produziu evidência explícita de latência por fonte, estados provisórios e falhas. Os limites decisivos são a persistência não reconciliada das consultas relacionadas, a recuperação não comprovada do Spotify em 26–27/08, a ausência de diff que quantifique a correção histórica da fase e a falta de teste formal de uso/desempenho da interface.

Fontes de evidência: Relatório Final de Auditoria e Congelamento (28/09/2026, RIR2026_FREEZE_1.0); auditoria pós-automação de 26/09; relatórios diários de 09, 16 e 20/09; Acompanhamento Complementar D+30 (13/10); leitura somente de metadados/contagens das tabelas do Supabase em 14/10/2026.