# Dicionário de dados e esquemas

Este dicionário registra esquemas vistos no código e nas tabelas/arquivos de saída. O esquema varia por fonte. Antes da submissão, gere o dicionário exato dos arquivos congelados e associe-o ao commit e a um manifesto SHA-256. Os nomes abaixo não substituem essa conferência.

## Convenções
- Data da fonte (data, data_ranking, data_publicacao) é distinta do timestamp da coleta (coletado_em/data_coleta).
- Google Trends é índice relativo/normalizado, não volume absoluto.
- Ausente em lista é nao_detectado, nunca zero de consumo. N/D, indisponível, não coletado e provisório permanecem distintos.
- Nulo não deve ser convertido automaticamente em zero. O projeto usa America/Sao_Paulo.

## Google Trends V2
Tabela trends_v2_interesse: artista_id, nome_artista, entidade, tipo_entidade, data_show, data, d_relativo, interesse, percentil_intra_artista, zscore_intra_artista, media_2026_intra, mediana_2026_intra, modo_busca, chave_google, periodo, is_partial, status_dado, data_validada_ate, metodologia.

Metadados trends_v2_entidades: artista_id, nome_artista, entidade, entidade_id, tipo_entidade, consulta_original, aliases, data_show, chave_google, titulo_google, tipo_topic_google, modo_busca, status_2026, status_baseline_2025, data_validada_ate, biblioteca_principal, fallback, related_topics_status, resolvido_em. Termo consultado, tópico selecionado e status baseline são dimensões distintas.

Baseline CSV: artista_id, nome_artista, entidade, tipo_entidade, data_show, data, interesse, modo_busca, chave_google, periodo, status_baseline, metodologia.

Sumário CSV: ranking_atencao_relativa, ranking_interesse_busca, artista_id, nome_artista, termo, tipo_entidade, modo_busca, chave_google, interesse_atual, percentil_atual, zscore_atual, media_interesse, mediana_2026, pico_interesse, data_pico, pontos_temporais, n_2025, status_baseline_2025, data_atual, data_validada_ate, status_dado, nota_metodologica.

Status CSV: versao, gerado_em, data_validada_ate, entidades_2026, entidades_baseline_2025, provisorio_disponivel_ate, related_topics, regra_comparacao, fonte.

## Spotify, presença e charts
spotify_artistas_diario.csv: data_ranking, artista_id, nome_artista, nome_normalizado, nome_spotify_esperado, spotify_artista_id, spotify_nome_artista, presente_top_200, quantidade_faixas, faixas_como_principal, faixas_como_participacao, melhor_posicao, streams_faixas_rankeadas, streams_7_dias_faixas_rankeadas. Cobertura limitada ao Top 200 e às faixas capturadas; não representa toda atividade do artista.

evolucao_presenca_rir.csv: data_referencia, tipo_data, artista_id, nome_artista, plataforma, tipo_item, periodicidade, titulo, posicao, movimento_posicao, valor, tipo_valor, fonte, origem_registro, prioridade_fonte, data_plataforma_confirmada, url_fonte, titulo_normalizado, titulo_comparacao, registro_id, tamanho_ranking, score_posicao, percentual_ranking_superado, faixa_score, elegivel_evolucao_diaria. Posição requer lista/tamanho; elegibilidade é variável derivada.

## TikTok e notícias
tiktok_rir_artistas.csv: data_ranking, fonte, tipo_ranking, artista_id, nome_artista, encontrado, ocorrencias_artista_fonte, posicao, musica, artista_fonte, criterio_match. Subfontes têm frescor desigual; ausência na lista consultada não significa ausência total na plataforma.

noticias_heineken_rir_publicacoes.csv: noticia_id, titulo, titulo_normalizado, veiculo, data_publicacao, data_publicacao_original, link, termo_consultado, categoria_consulta, assunto, relacao_rock_in_rio, data_coleta, coletado_em, url_rss, primeira_coleta, ultima_coleta, quantidade_coletas, url_original_google, url_final, status_decodificacao, erro_decodificacao, status_acesso, status_http, lead_noticia, origem_lead, arquivo_html_pagina, erro_acesso, categoria_validada, status_validacao, criterio_validacao, incluir_dashboard, nivel_confianca, status_processamento, validado_em, data, pauta_id. Por padrão, não redistribuir textos/HTML integrais.

Spotify/Kworb: scripts gravam ranking e créditos separados, com data, lista, posição/movimento, IDs e nomes, métricas publicadas, URL e timestamp. Confirmar cabeçalhos no CSV congelado antes de citar versão específica.

## Estados, chaves e trilha
| Estado | Significado |
|---|---|
| observado | resposta recebida e validada |
| provisorio | resposta recente sujeita a maturação |
| nao_detectado | entidade ausente da lista consultada |
| indisponivel | fonte/endpoint falhou, por exemplo HTTP 429 |
| nao_coletado | tarefa não executada ou período não coberto |
| n_d | valor não disponível/válido segundo método ou fonte |
| zero_valido | zero explícito retornado pela fonte |

Chave lógica recomendada: fonte + ID da entidade + data de referência + métrica + lista/dimensão + versão do tratamento. Logs devem ter chave própria e registrar lote, tentativa, status HTTP, latência, timestamp e versão do código.