# Catálogo de módulos do artefato

Este catálogo identifica o código publicado que compõe o observatório. Os arquivos são módulos do sistema construído; os rótulos indicam sua função no projeto.

## Google Trends
| Módulo | Papel observado no artefato |
|---|---|
| `scripts/coleta_google_trends_rir.py` | Coleta Trends no pipeline legado. |
| `scripts/trends_v2_runner.py` | Orquestra execução V2. |
| `scripts/trends_v2_pipeline.py` | Coleta, estrutura e consolida séries V2. |
| `scripts/coleta_google_trends_consultas_relacionadas.py` | Rotina de consultas relacionadas. |
| `scripts/coleta_google_trends_estados_7d.py` | Saída regional em janela de sete dias. |
| `scripts/sincroniza_trends_v2_storage.py` | Sincroniza saídas V2 com armazenamento. |
| `scripts/teste_google_trends_brasil.py` | Verificação técnica da fonte Trends Brasil. |

## Rankings, perfis e conteúdo
| Módulo | Papel observado no artefato |
|---|---|
| `scripts/coleta_spotify_historico_brasil.py` | Histórico do ranking Spotify Brasil. |
| `scripts/coleta_spotify_kworb.py` | Ranking diário e créditos extraídos de Kworb. |
| `scripts/coleta_charts_brasil.py` | Charts nacionais monitorados. |
| `scripts/coleta_tiktok_diaria.py` | Listas TikTok por subfonte. |
| `scripts/coleta_noticias_heineken_rir.py` | Corpus editorial ligado a Heineken/Rock in Rio. |
| `scripts/coleta_programacao.py` | Programação e datas de apresentações. |
| `scripts/coleta_perfis_artistas_rir.py` | Perfis públicos do lineup. |
| `scripts/coleta_paginas_individuais_kworb.py` | Páginas individuais Kworb. |
| `scripts/extrai_paginas_individuais_brasil.py` | Páginas individuais de charts brasileiros. |
| `scripts/audita_fontes_kworb.py` | Auditoria estrutural de fontes Kworb. |
| `scripts/inspeciona_plataformas_kworb.py` | Inventário de páginas/plataformas Kworb. |
| `scripts/teste_kworb.py` | Teste de parsing Kworb. |
| `scripts/teste_fonte_programacao.py` | Teste da fonte de programação. |

## Mapeamento, consolidação e métricas
| Módulo | Papel observado no artefato |
|---|---|
| `scripts/completa_mapeamento_spotify.py` | Complementa IDs Spotify do lineup. |
| `scripts/preenche_mapeamento_spotify.py` | Preenche mapeamento Spotify. |
| `scripts/cruza_spotify_rir.py` | Cruza Spotify com elenco do evento. |
| `scripts/cruza_spotify_historico_rir.py` | Cruza histórico Spotify. |
| `scripts/cruza_charts_brasil_rir.py` | Cruza charts brasileiros com lineup. |
| `scripts/consolida_presenca_atual_rir.py` | Consolida presença nas fontes. |
| `scripts/cria_metricas_presenca_rir.py` | Métricas de presença/cobertura. |
| `scripts/gera_tiktok_rir_artistas.py` | Correspondência das listas TikTok ao lineup. |
| `scripts/valida_noticias_heineken_rir.py` | Valida/classifica corpus editorial. |
| `scripts/gera_frescor_fontes.py` | Medidas de frescor/atraso das fontes. |

## Persistência, integridade e relatórios
| Módulo | Papel observado no artefato |
|---|---|
| `scripts/sincroniza_supabase.py` | Sincronização de tabelas. |
| `scripts/sincroniza_tiktok_supabase.py` | Sincronização específica TikTok. |
| `scripts/exporta_snapshot_tiktok_supabase.py` | Exportação de snapshot TikTok. |
| `scripts/valida_integridade_projeto.py` | Checagens de integridade. |
| `scripts/registra_diario_projeto.py` | Registro de execução/estado diário. |
| `scripts/gera_esqueleto_relatorio_artigo_diario.py` | Relatório diário a partir do estado do projeto. |
| `scripts/atualiza_projeto_rir.py` | Fluxo geral de atualização. |
| `scripts/atualiza_projeto_rir_sem_trends.py` | Atualização geral sem Trends. |
| `scripts/corrige_fase_monitoramento.py` | Correção operacional da fase 08–10/09. |

## Preparação de visualização
| Módulo | Papel observado no artefato |
|---|---|
| `scripts/prepara_modelo_power_bi.py` | Preparação de dados para Power BI. |
| `scripts/prepara_noticias_dashboard.py` | Preparação do corpus editorial para visualização. |
| `scripts/prepara_noticias_dashboard_marca.py` | Preparação do recorte de marca. |
| `scripts/prepara_perfis_dashboard.py` | Preparação de perfis para interface. |

## Execução auditada

O freeze registra Actions #40 concluída com sucesso em 27/09/2026. A auditoria de 26/09 registra execução pós-automação #39 e reconciliação de 73/73 arquivos e 28/28 snapshots sem erro naquele teste. O código publicado não contém credenciais. As tabelas e os snapshots necessários para repetir todas as execuções não acompanham o repositório.