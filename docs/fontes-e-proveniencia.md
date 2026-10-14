# Inventário de fontes e proveniência

## Fontes observadas

| Fonte | O que fornece no projeto | Regra de interpretação | Frescor no freeze 28/09/2026 | Redistribuição |
|---|---|---|---|---|
| Google Trends V2 | Série de interesse por entidade/Topic no Brasil; baseline 2025 quando validado | Índice normalizado; comparar trajetória da própria entidade; preservar N/D e provisórios | Consolidado até 23/09; 24–25/09 provisórios | Reconsultar origem; não afirmar que índice é volume absoluto |
| Spotify Charts Brasil | Presença e streams das faixas que entram no Top 200 | Ranking censurado; ausência não é zero nem consumo total | 25/09 | Verificar termos/API/licença antes de republicar snapshots |
| Charts nacionais | Posição/presença por fonte (Apple Music, iTunes, Deezer, Shazam etc.) | Manter identidade de cada chart; não somar cegamente | Snapshot de integridade até 27/09 | Conteúdo/frequência sujeito a termos dos serviços |
| TikTok / KWORB / TrendingTikTokSongs | Posições/listas e histórico disponível em cada subfonte | Lista monitorada/circulação; ausência não significa zero vídeos ou visualizações | KWORB/histórico 27/09; TrendingTikTokSongs 25/09 | Verificar termos de cada site; não republicar HTML ou mídia |
| Programação oficial do Rock in Rio | Datas/palcos/lineup e chave de amostra | Validar lineup e manter changelog | 28 apresentações; 7 dias; 4 por dia | Citar página oficial e data de acesso |
| Corpus editorial Heineken | Metadados de cobertura editorial e classificações de tópico | Fora da pergunta principal; manter proveniência e deduplicação | 117 registros editoriais, última publicação 16/09 | Não republicar texto integral nem imagens sem autorização |
| Google Analytics / uso da plataforma | Métricas prospectivas de acesso após instrumentação | Não reconstruir retrospectivamente 08/09 | Instrumentação prospectiva desde 09/09 segundo relatório | Dados agregados e privacidade conforme configuração |

## Linhagem

1. **Coleta:** workflows/scripts versionados executam por fonte; log deve guardar versão, timestamp/fuso, parâmetros, erros e tentativa.
2. **Tratamento:** IDs, status, datas, deduplicação e estado de maturação são aplicados por regras específicas e documentadas.
3. **Armazenamento:** Supabase guarda tabelas operacionais; GitHub guarda código, documentação, snapshots/metadados permitidos e relatórios de integridade.
4. **Relato diário:** monitora execução, frescor e resultados; é trilha de auditoria, não substitui os dados de origem.
5. **Congelamento:** corte principal em 28/09/2026, commit de dados citado no relatório como `f508aaa78631ecddbedcb4bd117c0b1041b2c17c`; alterações posteriores são complementares.
6. **Pacote público:** esta versão exclui dados brutos e conteúdos protegidos enquanto não houver verificação documental de direitos. O manifest público deve incluir SHA-256 dos arquivos redistribuídos e referência ao commit final do pacote.

## Relatórios diários examinados

Foram considerados o diário metodológico no repositório de desenvolvimento; auditoria Supabase/baseline de 03/09; relatórios interpretativos com ressalvas de Trends legado e instrumentação Analytics; auditorias pós-festival de 23–26/09; relatório de congelamento de 28/09; e checkpoint complementar D+30 de 13/10. As datas efetivas variam por fonte; o D+30 não é um snapshot completo D+30 e não altera o freeze.

## Pendências de proveniência

- Confirmar lacuna/backfill de Spotify em 26–27/08 com teste de presença diária no snapshot, não com contagem agregada.
- Gerar hashes SHA-256 e publicar o manifest final dos arquivos redistribuídos.
- Definir política de licença para código e dados próprios.
- Inserir as URLs exatas e datas de acesso para cada página/API consultada.
- Verificar termos de republicação por fonte antes de adicionar qualquer dado bruto ao diretório `data/`.
