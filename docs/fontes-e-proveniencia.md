# Fontes utilizadas e proveniência registrada

## Fontes efetivamente integradas

| Fonte/camada | Objeto coletado no projeto | Corte científico de 28/09 | Limite observado |
|---|---|---|---|
| Programação oficial do Rock in Rio | Lineup e datas do Palco Mundo | 28 artistas/apresentações configurados; 7 dias, 4 por dia | Define o recorte; alterações de programação requerem versão separada. |
| Google Trends V2 | Interesse de busca por entidade; baseline e distribuição regional em saídas separadas | 8.040 linhas/30 entidades; consolidadas até 23/09, parciais até 25/09; baseline 1.537/29 entidades | Índice normalizado, não volume absoluto; 60 linhas recentes provisórias. |
| Spotify Top 200 Brasil | Presença e streams de faixas listadas; agregação por artista a partir de faixas mapeadas | 5.800 linhas, data efetiva até 25/09 | Só cobre faixas que aparecem no Top 200; auditoria havia apontado 26–27/08 ausentes. |
| Charts nacionais (Apple Music, iTunes, Deezer, Shazam e outras capturadas) | Presença e posição por chart | 24 métricas no snapshot de integridade, referência até 27/09 | Listas e profundidades diferentes; posição não equivale a audiência. |
| TikTok/KWORB/TrendingTikTokSongs | Listas atuais e histórico disponível por subfonte | KWORB 2.592 linhas; rankings 1.150; histórico 621; últimas datas variam entre 25 e 27/09 | Fonte/lista monitorada não cobre toda circulação TikTok. |
| Corpus editorial Heineken/Google Notícias | Metadados, data de publicação, veículo e classificação temática | 117 publicações; última publicação registrada em 16/09 | Corpus auxiliar; não mede impacto musical e não autoriza republicar matéria integral. |
| Analytics da interface | Eventos de navegação da SPA adicionados ao site | Instrumentação prospectiva desde 09/09; sem série de uso validada no freeze consultado | Não havia base para estimar acessos de 08/09 retrospectivamente. |

## Linhagem efetivamente documentada

1. Scripts de coleta e tratamento estão versionados em GitHub; workflows Actions executam etapas automatizadas.
2. Tabelas operacionais e arquivos foram mantidos em Supabase; arquivos e documentos de execução também aparecem no histórico do projeto.
3. Relatórios diários registram horários, datas efetivas, frescor, estados de maturação, alterações de método e exceções.
4. O relatório de congelamento referencia o commit de dados `f508aaa78631ecddbedcb4bd117c0b1041b2c17c` e o commit de documentação do cutoff `73fe7639ddfc654a16333c15d9fd785937b9b4fa`.
5. O congelamento científico é 28/09/2026 16:32:48 BRT, versão RIR2026_FREEZE_1.0.
6. O checkpoint D+30 de 13/10 é posterior e incompleto por fonte; permanece suplementar.

## Estado posterior consultado em 14/10/2026

No Supabase, a tabela `trends_v2_interesse` continuava com 8.040 linhas e 60 parciais; `trends_v2_baseline_2025`, 1.537 linhas; `trends_v2_consultas`, zero linhas; `trends_v2_regioes`, 789 linhas. As tabelas TikTok em operação haviam crescido a 4.128 linhas KWORB, 1.847 rankings e 1.729 históricas, com data efetiva até 13/10. Esses números posteriores não são contagens do freeze.

## Situação de distribuição

Os arquivos tratados e snapshots versionados estão acessíveis no repositório operacional no commit de dados `f508aaa78631ecddbedcb4bd117c0b1041b2c17c`; este dossiê inclui um manifesto dos 138 arquivos com tamanho e Git blob SHA. Esse identificador Git não é SHA-256. Os relatórios integrais de trabalho permanecem no Drive; não são necessários para baixar o corte público, mas fundamentam a trilha de auditoria.

Os termos de redistribuição das plataformas não foram comprovados para todos os arquivos; por isso não se publicaram HTML, capturas integrais, notícias, imagens nem dumps completos. O acesso às fontes originais permanece necessário para reexecutar coletas, sujeito à disponibilidade atual.