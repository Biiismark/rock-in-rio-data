# Rock in Rio 2026 — evidências do observatório digital

Este repositório documenta o **artefato construído e operado** no projeto Rock in Rio 2026: um observatório que reuniu código de coleta, tratamento, armazenamento, rotinas de validação, relatórios e interface de consulta para acompanhar indicadores públicos ligados ao Palco Mundo.

O artigo associado avalia o ferramental e sua operação. Os indicadores de artistas são evidência de cobertura e funcionamento das fontes; este trabalho não estima crescimento individual nem atribui efeito causal ao festival.

## O que foi realizado

- Configuração de 28 artistas em sete datas do Palco Mundo, quatro apresentações por dia.
- Coleta e tratamento de séries de Google Trends V2, Spotify Top 200 Brasil, charts nacionais, listas e históricos TikTok, programação e corpus editorial da Heineken.
- Código Python e workflows GitHub Actions; armazenamento em Supabase e arquivos versionados; interface web de consulta.
- Protocolo com data do evento, data efetiva da fonte e timestamp de coleta separados; estados de observado, provisório, não detectado, N/D e indisponível preservados.
- Auditorias diárias, correções operacionais e congelamento científico RIR2026_FREEZE_1.0 em 28/09/2026 às 16:32:48 BRT.

## Resultado do corte científico

| Camada | Evidência no congelamento |
|---|---|
| Programação | 28 apresentações/artistas; 7 datas; 4 por data |
| Google Trends V2 | 8.040 observações para 30 entidades; 7.980 consolidadas até 23/09 e 60 provisórias de 24–25/09 |
| Baseline Trends 2025 | 1.537 observações para 29 entidades; Nova Twins permanece N/D |
| Checkpoints Trends | D0, D+1, D+3 e D+7: 112/112 consolidados |
| Spotify diário | 5.800 linhas; data efetiva até 25/09 |
| Charts | 24 métricas de presença no snapshot de integridade, referência até 27/09 |
| TikTok | 2.592 linhas KWORB, 1.150 de rankings, 621 de histórico no freeze; lineup: 0/28 detectados nas listas monitoradas |
| Heineken editorial | 117 publicações; última publicação do corte em 16/09 |
| Automação/integridade | GitHub Actions #40 concluída com sucesso em 27/09; integridade final registrada como OK |

**O que esses números sustentam:** cobertura estrutural, conclusão dos checkpoints definidos e preservação de estados/latências. Não demonstram eficácia causal do festival, redução mensurada dos erros após backoff, recuperação do Spotify em 26–27/08 ou usabilidade/performance validada da interface.

## Evidências e registros

- [Relatório oficial de auditoria do congelamento (PDF)](docs/evidencias/Relatorio_Final_Auditoria_Congelamento_Rock_in_Rio_2026_2026-09-28.pdf)
- [Resultados e avaliação do artefato](docs/resultados-e-avaliacao.md)
- [Trilha de evidências e lacunas de rastreabilidade](docs/auditoria-de-evidencias.md)
- [Registro dos relatórios diários, incidentes e divergências](docs/relatorios-de-evidencia.md)
- [Matriz técnica de questionamentos](docs/matriz-tecnica.md)
- [Registro de falhas realmente observadas e respostas implementadas](docs/falhas-e-solucoes.md)
- [Protocolo executado no projeto](docs/protocolo.md)
- [Dicionário das tabelas e saídas](docs/dicionario-de-dados.md)
- [Fontes, datas efetivas e proveniência](docs/fontes-e-proveniencia.md)
- [Catálogo do código que compõe o artefato](docs/catalogo-codigo.md)
- [Referências mobilizadas no manuscrito](docs/referencias.md)
- [Inventário factual das contagens do congelamento](data/inventario-congelamento-2026-09-28.csv)
- [Acesso ao corte público e limites da reprodução](docs/acesso-ao-corte-e-reproducao.md)
- [Manifesto dos 138 arquivos de dados no commit congelado](data/manifesto-dados-publicos-freeze-1.0.csv)
- [Metadados originais do congelamento: manifesto JSON](data/congelamento/manifesto_congelamento.json)
- [Status das fontes no cutoff](data/congelamento/estado_fontes_cutoff.csv)
- [Dados resumidos dos checkpoints D0–D+7](data/congelamento/checkpoints_d0_d1_d3_d7.csv)
- [Verificador de integridade do snapshot](scripts/verificar_manifesto_snapshot.py)
- [Dados e código no commit imutável do repositório de origem](https://github.com/Biiismark/rock-in-rio-2026/tree/f508aaa78631ecddbedcb4bd117c0b1041b2c17c/dados)

## Evidência complementar de 13/10

O checkpoint chamado D+30 não contém uma fotografia completa em D+30. Em 13/10, Trends chegava a 25/09 (consolidado até 23/09), Spotify a 11/10 (D+28), charts e TikTok a 12/10 (D+29), e Heineken a 09/10. Essa atualização é complementar e não altera o congelamento primário.

## Acesso aos dados e limite atual de reprodução

O conjunto congelado está publicamente acessível no repositório de origem, no commit de dados `f508aaa78631ecddbedcb4bd117c0b1041b2c17c`. Esse corte contém 138 arquivos em `dados/` (28.035.375 bytes). O [manifesto do corte](data/manifesto-dados-publicos-freeze-1.0.csv) registra caminhos, tamanhos, Git blob SHAs e links imutáveis. A pasta não foi duplicada neste dossiê para evitar cópias divergentes; o acesso e a forma de reproduzir estão descritos em [Acesso ao corte público e limites da reprodução](docs/acesso-ao-corte-e-reproducao.md).

O conjunto de dados e o código do corte podem ser inspecionados e usados para conferir os resultados. Ainda não foi executada uma reprodução independente, comando a comando, de todas as tabelas finais do manuscrito; portanto, não afirmamos que essa validação já foi concluída. Coletas externas também dependem da disponibilidade e dos termos das fontes.

O estado do código e da documentação é público, mas ainda não foi declarada licença de reutilização para os materiais próprios; dados e conteúdo de terceiros permanecem sujeitos aos termos das fontes. A publicação permite acesso para avaliação, sem conceder automaticamente direitos amplos de redistribuição.

## Âncoras de versão

- Versão científica: RIR2026_FREEZE_1.0; corte em 28/09/2026 16:32:48 BRT.
- Commit de dados de referência registrado no relatório de congelamento: `f508aaa78631ecddbedcb4bd117c0b1041b2c17c`.
- Commit de documentação do cutoff registrado no relatório: `73fe7639ddfc654a16333c15d9fd785937b9b4fa`.
- Projeto Supabase consultado para auditoria posterior: `rock-in-rio-2026`.

## Citação

Aguiar, B. (2026). *Rock in Rio 2026: evidências do observatório digital e de sua avaliação técnica* [Código e documentação]. GitHub. https://github.com/Biiismark/rock-in-rio-data
