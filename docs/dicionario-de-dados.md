# Dicionário de dados — esquema do projeto

Esquemas abaixo foram verificados nas tabelas `public` do Supabase em 14/10/2026. As contagens são fotografia operacional dessa consulta; onde anotado, não correspondem ao freeze. As tabelas operacionais atuais são distintas dos CSVs públicos do corte fixado no repositório de origem.

## Google Trends V2

| Tabela | Linhas em 14/10 | Chave primária | Colunas e tipos observados |
|---|---:|---|---|
| `trends_v2_interesse` | 8.040 | `artista_id, data` | `artista_id:text; nome_artista:text; entidade:text; tipo_entidade:text; data_show:date; data:date; d_relativo:integer; interesse:numeric; percentil_intra_artista:numeric; zscore_intra_artista:numeric; media_2026_intra:numeric; mediana_2026_intra:numeric; modo_busca:text; chave_google:text; periodo:text; is_partial:boolean; status_dado:text; data_validada_ate:date; metodologia:text; atualizado_em:timestamptz` |
| `trends_v2_baseline_2025` | 1.537 | `artista_id, data` | `artista_id:text; nome_artista:text; entidade:text; tipo_entidade:text; data_show:date; data:date; interesse:numeric; modo_busca:text; chave_google:text; periodo:text; status_baseline:text; metodologia:text; atualizado_em:timestamptz` |
| `trends_v2_entidades` | 30 | `artista_id` | `artista_id:text; nome_artista:text; entidade:text; entidade_id:integer; tipo_entidade:text; consulta_original:text; aliases:text; data_show:date; chave_google:text; titulo_google:text; tipo_topic_google:text; modo_busca:text; status_2026:text; status_baseline_2025:text; data_validada_ate:date; biblioteca_principal:text; fallback:text; related_topics_status:text; resolvido_em:timestamptz; atualizado_em:timestamptz` |
| `trends_v2_consultas` | 0 | `artista_id, consulta_relacionada, tipo_consulta` | `artista_id:text; nome_artista:text; entidade:text; consulta_relacionada:text; valor_google:numeric; tipo_consulta:text; indicador_movimento:text; explodiu:boolean; valor_exibicao:text; periodo_dias:text; tipo_relacao:text; modo_busca:text; data_validada_ate:date; metodologia:text; atualizado_em:timestamptz` |
| `trends_v2_regioes` | 789 | `artista_id, estado` | `artista_id:text; nome_artista:text; entidade:text; estado:text; geo_code:text; indice_estado_termo:numeric; modo_busca:text; data_validada_ate:date; metodologia:text; atualizado_em:timestamptz` |
| `trends_v2_resumo` | 30 | `artista_id` | `artista_id:text; nome_artista:text; entidade:text; tipo_entidade:text; modo_busca:text; chave_google:text; interesse_atual:numeric; percentil_atual:numeric; zscore_atual:numeric; media_interesse:numeric; mediana_2026:numeric; pico_interesse:numeric; data_pico:date; pontos_temporais:integer; n_2025:integer; status_baseline_2025:text; data_atual:date; data_validada_ate:date; status_dado:text; nota_metodologica:text; atualizado_em:timestamptz` |
| `trends_v2_status` | 1 | `versao` | `versao:text; gerado_em:date; data_validada_ate:date; entidades_2026:integer; entidades_baseline_2025:integer; provisorio_disponivel_ate:date; related_topics:text; regra_comparacao:text; fonte:text; atualizado_em:timestamptz` |

## TikTok

| Tabela | Linhas em 14/10 | Chave primária | Colunas e tipos observados |
|---|---:|---|---|
| `tiktok_kworb` | 4.128 | `data_ranking, posicao` | `data_ranking:date; data_execucao:date; plataforma:text; fonte:text; tipo_ranking:text; pais:text; posicao:integer; variacao:text; artista:text; artista_normalizado:text; musica:text` |
| `tiktok_rankings` | 1.847 | `data_ranking, tipo_ranking, posicao` | `data_ranking:date; data_execucao:date; plataforma:text; fonte:text; tipo_ranking:text; pais:text; posicao:integer; artista:text; artista_normalizado:text; musica:text; videos_tiktok:bigint; url_som:text` |
| `tiktok_historico` | 1.729 | `data, url_som` | `data:date; artista:text; musica:text; rank:integer; novos_videos_tiktok:bigint; videos_tiktok_acumulados:bigint; url_som:text; origem_historico:text; data_execucao:date; primeira_aparicao:date; ultima_aparicao:date; pico_data:date; pico_posicao:integer; dias_no_chart:integer` |
| `tiktok_resumo_sons` | 150 | `url_som` | `url_som:text; artista:text; musica:text; videos_tiktok_atual:bigint; uso_7d:bigint; variacao_7d_pct:numeric; rank_7d_texto:text; pico_posicao:integer; pico_data:date; sequencia_atual_dias:integer; dias_no_chart:integer; primeira_aparicao:date; ultima_aparicao:date; paises:integer; datas_visiveis_extraidas:integer; datas_embutidas_extraidas:integer; datas_iso_candidatas_html:integer` |
| `tiktok_auditoria_historico` | 9 | `url_som` | `url_som:text; musica:text; datas_extraidas:integer; dias_no_chart_resumo:integer; primeira_aparicao:date; ultima_aparicao:date; min_data_extraida:date; max_data_extraida:date` |

## Campos centrais e interpretação

| Campo | Significado no projeto |
|---|---|
| `data_show` | Data da apresentação usada para alinhar a série ao evento. |
| `data` / `data_ranking` | Data representada pela série ou ranking, distinta do horário de coleta. |
| `d_relativo` | Distância em dias à apresentação, calculada pela regra do projeto. |
| `interesse` | Índice relativo do Google Trends; não é contagem de buscas. |
| `percentil_intra_artista`, `zscore_intra_artista` | Transformações calculadas dentro da série do próprio artista. |
| `is_partial`, `status_dado` | Estado de parcialidade/validação; 60 linhas recentes do freeze estão marcadas provisórias. |
| Posição/presença em ranking | Aparecer ou não numa lista delimitada; ausência é não detecção, não consumo zero. |
| `data_execucao` | Data operacional da coleta; não substitui `data_ranking`. |

As chaves listadas são as declaradas no schema consultado. Campos nullable podem estar vazios porque a fonte não os forneceu ou porque a etapa não se aplicou. Nulo, ausência de linha, não detecção, N/D e indisponibilidade não são estados equivalentes.

`trends_v2_bootstrap_files` continha metadados de um arquivo `google_trends_v2_status.csv` (hash e tamanho) atualizado em 10/09/2026. O conteúdo codificado não é reproduzido. O [manifesto público do corte](../data/manifesto-dados-publicos-freeze-1.0.csv) registra Git blob SHAs e tamanhos para os 138 arquivos; esses identificadores Git não são SHA-256.