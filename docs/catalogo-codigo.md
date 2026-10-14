# Catálogo do código

Os nomes descrevem o papel principal dos scripts. Alguns têm funções secundárias. A execução independente pode exigir credenciais, acesso às fontes, dependências e schema configurados. Confira termos vigentes antes de executar coletas.

## Coleta e extração

| Script | Função principal |
|---|---|
| scripts/coleta_google_trends_rir.py | Consulta séries Google Trends do projeto. |
| scripts/trends_v2_runner.py | Orquestra a execução Trends V2. |
| scripts/trends_v2_pipeline.py | Coleta, consolida e gera saídas Trends V2. |
| scripts/coleta_google_trends_consultas_relacionadas.py | Coleta consultas relacionadas quando disponíveis. |
| scripts/coleta_google_trends_estados_7d.py | Consulta distribuição regional em janela de sete dias. |
| scripts/teste_google_trends_brasil.py | Verifica comportamento da fonte Trends Brasil. |
| scripts/coleta_spotify_historico_brasil.py | Coleta histórico do ranking Spotify Brasil. |
| scripts/coleta_spotify_kworb.py | Extrai ranking diário e créditos da página pública Kworb. |
| scripts/coleta_charts_brasil.py | Coleta charts brasileiros monitorados. |
| scripts/coleta_tiktok_diaria.py | Coleta rankings diários das fontes TikTok configuradas. |
| scripts/coleta_noticias_heineken_rir.py | Busca publicações editoriais relacionadas a Heineken/Rock in Rio. |
| scripts/coleta_programacao.py | Coleta dados da programação do evento. |
| scripts/coleta_perfis_artistas_rir.py | Coleta/atualiza perfis públicos dos artistas. |
| scripts/coleta_paginas_individuais_kworb.py | Extrai páginas individuais de artistas no Kworb. |
| scripts/extrai_paginas_individuais_brasil.py | Extrai páginas individuais de charts brasileiros. |
| scripts/audita_fontes_kworb.py | Audita disponibilidade e estrutura de fontes Kworb. |
| scripts/inspeciona_plataformas_kworb.py | Inspeciona páginas e plataformas disponíveis em Kworb. |
| scripts/teste_kworb.py | Testa extração/interpretação de páginas Kworb. |
| scripts/teste_fonte_programacao.py | Testa a fonte de programação. |

## Normalização, integração e métricas

| Script | Função principal |
|---|---|
| scripts/completa_mapeamento_spotify.py | Completa vínculos entre artistas e IDs Spotify. |
| scripts/preenche_mapeamento_spotify.py | Preenche registros do mapeamento Spotify. |
| scripts/cruza_spotify_rir.py | Cruza registros Spotify com elenco do evento. |
| scripts/cruza_spotify_historico_rir.py | Cruza histórico Spotify com artistas do evento. |
| scripts/cruza_charts_brasil_rir.py | Cruza rankings brasileiros com artistas do evento. |
| scripts/consolida_presenca_atual_rir.py | Consolida presença atual nas fontes monitoradas. |
| scripts/cria_metricas_presenca_rir.py | Gera métricas de presença e cobertura. |
| scripts/gera_tiktok_rir_artistas.py | Gera registros TikTok associados aos artistas monitorados. |
| scripts/valida_noticias_heineken_rir.py | Valida/classifica notícias coletadas. |
| scripts/gera_frescor_fontes.py | Calcula e relata atualidade/atraso das fontes. |

## Sincronização, validação e relatórios

| Script | Função principal |
|---|---|
| scripts/sincroniza_supabase.py | Sincroniza tabelas com Supabase. |
| scripts/sincroniza_tiktok_supabase.py | Sincroniza dados TikTok com Supabase. |
| scripts/sincroniza_trends_v2_storage.py | Sincroniza saídas Trends V2 com armazenamento configurado. |
| scripts/exporta_snapshot_tiktok_supabase.py | Exporta snapshot TikTok do Supabase. |
| scripts/valida_integridade_projeto.py | Executa verificações de integridade. |
| scripts/registra_diario_projeto.py | Registra eventos no diário do projeto. |
| scripts/gera_esqueleto_relatorio_artigo_diario.py | Prepara esqueleto de relatório diário. |
| scripts/atualiza_projeto_rir.py | Atualiza o fluxo geral, incluindo fontes configuradas. |
| scripts/atualiza_projeto_rir_sem_trends.py | Atualiza o fluxo sem Google Trends. |
| scripts/corrige_fase_monitoramento.py | Corrige classificação de fase para registros elegíveis. |

## Saídas e dashboards

| Script | Função principal |
|---|---|
| scripts/prepara_modelo_power_bi.py | Prepara entradas do Power BI. |
| scripts/prepara_noticias_dashboard.py | Prepara notícias para dashboard. |
| scripts/prepara_noticias_dashboard_marca.py | Prepara notícias de marca para dashboard. |
| scripts/prepara_perfis_dashboard.py | Prepara perfis para dashboard. |

## Cautelas de reprodução

- Trends V2 aplica pausas aleatórias de 65–85 s entre consultas e aguarda 300 s após HTTP 429 antes da tentativa seguinte. Isso aumenta o tempo de extração. Não foi medida comparativamente a taxa de falhas antes/depois.
- Código público não inclui credenciais. A execução requer configuração própria; respostas podem variar com data, localidade, plataforma e biblioteca.
- Publicar código não autoriza redistribuir snapshots, HTML ou conteúdo de terceiros.