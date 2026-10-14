# Protocolo executado no observatório

## Desenho e objeto

O projeto foi um relato tecnológico aplicado e descritivo, orientado pela construção e avaliação de um artefato digital. O objeto avaliado foi o observatório em operação, composto por scripts, regras de tratamento, armazenamento, versionamento, automações, relatórios e interface. O estudo não foi desenhado para identificar efeito causal do festival.

## Recorte realizado

- Evento e palco: Rock in Rio 2026, Palco Mundo.
- Unidade de configuração: 28 artistas em sete datas, quatro apresentações por data.
- Território das fontes nacionais: Brasil, conforme a cobertura própria de cada serviço.
- Janela de observação: baseline pré-evento e observações ao redor dos shows; Google Trends usou checkpoints D0, D+1, D+3 e D+7.
- Congelamento científico: RIR2026_FREEZE_1.0, corte 28/09/2026 às 16:32:48 BRT.
- Observações posteriores foram mantidas na camada operacional/complementar. O relatório D+30 de 13/10 não atualizou o corte primário.

## Fontes e dados observados

O sistema reuniu programação oficial, Google Trends, Spotify Top 200 Brasil, charts nacionais, listas/históricos TikTok e corpus editorial da Heineken. Cada fonte foi mantida em sua unidade original. Índices de busca, posição de ranking, presença em lista, contagem de itens e publicação editorial não foram somados como se fossem a mesma métrica.

No corte de 28/09, o relatório registra 8.040 observações Trends para 30 entidades; 7.980 consolidadas até 23/09 e 60 provisórias de 24–25/09. O baseline de 2025 tinha 1.537 observações e 29 entidades; Nova Twins permaneceu N/D. Os quatro checkpoints definidos somaram 112/112 observações consolidadas.

## Tratamento executado

1. Os registros preservaram identificador e nome da entidade, termo/Topic consultado quando disponível, data efetiva e estado da fonte.
2. Data do evento, data de referência da fonte e timestamp da coleta foram mantidos separados quando presentes.
3. Ausência em lista foi interpretada como não detecção na lista consultada, não como zero de consumo.
4. Ausência de baseline e falha de endpoint permaneceram estados explícitos; valores não foram imputados para preencher lacunas.
5. Dados recentes sujeitos à maturação ficaram marcados como provisórios e foram separados dos consolidados.
6. Correções posteriores e coletas após 28/09 foram mantidas fora do corte científico.
7. Para Trends V2, as séries foram tratadas por entidade, com medidas intra-artista; o índice da plataforma não foi tratado como volume absoluto.

## Evolução operacional relevante

A auditoria de 03/09 registrou instabilidade no pipeline Trends legado, um HTTP 429 em consultas relacionadas e a regra de classificação indevida para 08–10/09. A documentação diária de 09/09 registra a V2 com coleta individual e metadados, além de 604 registros de related queries naquela saída. Código posterior aumentou o intervalo entre chamadas para 65–85 segundos e definiu espera de 300 segundos após 429. A tabela SQL de related queries estava vazia na leitura de 14/10, divergência ainda não reconciliada.

O script e workflow de correção da fase 08–10/09 foram confirmados posteriormente. A alteração da regra operacional não foi acompanhada por diff/contagem pública das linhas alteradas no snapshot.

## Critérios e resultado da avaliação

A avaliação disponível foi documental e estrutural. O freeze registra Actions #40 bem-sucedida em 27/09 e status de integridade OK para as fontes auditadas. A auditoria pós-automação de 26/09 registrou 73/73 arquivos e 28/28 snapshots sincronizados, sem erro no teste correspondente.

Não foram localizados teste formal de usabilidade, medição de disponibilidade/tempo de resposta do site nem avaliação com participantes. Os dados e o código do congelamento estão publicamente acessíveis no commit `f508aaa78631ecddbedcb4bd117c0b1041b2c17c`; a reprodução independente de todas as tabelas do manuscrito ainda não foi realizada.

## Limites

Os resultados são limitados pela latência e cobertura distintas das fontes, pela censura de rankings, pela normalização/possível reamostragem do Trends, pela lacuna Spotify 26–27/08 ainda não auditada e pela divergência sobre persistência de related queries V2. O corte e o código estão distribuídos no commit público `f508aaa78631ecddbedcb4bd117c0b1041b2c17c`; a reprodução independente dos resultados do manuscrito continua pendente.