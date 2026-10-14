# Acesso ao conjunto de dados congelado

## Referência imutável

O pacote público de avaliação usa o conjunto de dados já versionado no repositório operacional do projeto:

- Repositório de código e dados: [Biiismark/rock-in-rio-2026](https://github.com/Biiismark/rock-in-rio-2026)
- Corte científico: **RIR2026_FREEZE_1.0**, 28/09/2026 às 16:32:48 (BRT)
- Commit de dados de referência: [`f508aaa78631ecddbedcb4bd117c0b1041b2c17c`](https://github.com/Biiismark/rock-in-rio-2026/commit/f508aaa78631ecddbedcb4bd117c0b1041b2c17c)
- Commit que registra o cutoff: [`73fe7639ddfc654a16333c15d9fd785937b9b4fa`](https://github.com/Biiismark/rock-in-rio-2026/commit/73fe7639ddfc654a16333c15d9fd785937b9b4fa)
- [Pasta `dados/` no corte imutável](https://github.com/Biiismark/rock-in-rio-2026/tree/f508aaa78631ecddbedcb4bd117c0b1041b2c17c/dados)
- [Arquivo compactado do commit](https://github.com/Biiismark/rock-in-rio-2026/archive/f508aaa78631ecddbedcb4bd117c0b1041b2c17c.zip)

O commit de cutoff contém **138 arquivos** sob `dados/`, totalizando **28.035.375 bytes**: tabelas tratadas, registros de auditoria, metodologia, referências e relatórios versionados. Os arquivos permanecem no repositório de origem; este dossiê não cria uma segunda cópia divergente.

## Manifesto verificável

[`data/manifesto-dados-publicos-freeze-1.0.csv`](../data/manifesto-dados-publicos-freeze-1.0.csv) lista cada arquivo do diretório `dados/` no commit fixado, seu tamanho em bytes, seu Git blob SHA e o link para o arquivo naquela versão. O Git blob SHA é o identificador do objeto Git, **não** um hash SHA-256.

Arquivos centrais do artigo ferramental incluem, entre outros:

- Google Trends V2: `dados/tratados/google_trends_v2_evolucao.csv`, `google_trends_v2_baseline_2025.csv`, `google_trends_v2_estados.csv`, `google_trends_v2_metadados.csv`, `google_trends_v2_resumo.csv` e `google_trends_v2_status.csv`.
- Spotify: `dados/tratados/spotify_historico_brasil.csv`, `spotify_rir_faixas_diario.csv` e arquivos de catálogo/créditos.
- Charts, TikTok, programação, auditorias e corpus editorial Heineken: caminhos e identificadores estão no manifesto.

## O que é possível reproduzir

O conjunto não está ausente: ele pode ser baixado e inspecionado pelo commit público fixado. Isso permite conferir as tabelas de dados e os resultados resumidos sem depender da cópia operacional atual no Supabase. Os workflows e scripts do mesmo repositório também estão vinculados àquele estado.

A coleta original em si depende de sites externos, disponibilidade das fontes, cotas e, em algumas rotinas, configuração local. Nenhuma credencial é publicada. Reexecutar uma coleta hoje não recria automaticamente o estado histórico de 28/09; a reprodução do corte deve usar os arquivos desse commit, sem trocar para a branch `main`.

Ainda falta uma validação independente, comando a comando, de cada tabela final do manuscrito contra esse corte. Por isso, o status correto é: **dados e código do corte estão publicamente acessíveis; reprodução integral de todas as tabelas do manuscrito ainda precisa ser executada e conferida**.

## Divergência específica do Google Trends relacionado

No corte do repositório existe um arquivo legado, `dados/tratados/google_trends_rir_consultas_relacionadas.csv`, com 157 linhas incluindo cabeçalho. Esse arquivo não é identificado como a tabela V2 de consultas relacionadas e não reconcilia, por si só, os 604 registros relatados no relatório diário de 09/09. Na consulta ao Supabase em 14/10, `trends_v2_consultas` tinha zero linhas. O estado desses registros V2 permanece sem reconciliação.

## Acesso, Drive e termos das fontes

O Drive permanece útil como arquivo de trabalho e trilha dos relatórios originais. Não é necessário apagá-lo para que o avaliador consulte a versão pública fixada. A existência dos dados no GitHub garante acesso ao corte, mas **não cria uma licença de redistribuição** para conteúdo de terceiros; os termos das fontes continuam aplicáveis. O pacote não publica credenciais, tokens ou chaves de acesso.
