# Dicionário conceitual de dados

O esquema varia por fonte. Antes da submissão, reconciliar esta tabela com os nomes exatos das colunas dos CSVs congelados e adicionar um CSV de dicionário exportado automaticamente.

| Campo conceitual | Tipo | Obrigatório | Definição / regra |
|---|---|---:|---|
| `fonte` | string/categoria | sim | Plataforma ou conjunto de origem (ex.: Google Trends V2, Spotify Top 200 BR, chart individual, TikTok KWORB). |
| `entidade_id` | string | sim | Identificador estável interno para artista, evento ou marca; não deve depender do nome renderizado. |
| `nome_entidade` | string | sim | Nome usado em interface/relatório; guardar separado do ID. |
| `consulta_original` | string | quando aplicável | Termo ou tópico realmente enviado à fonte. |
| `chave_google` | string | Trends | Topic/MID selecionado e validado; guardar tipo de busca e rótulo. |
| `data_evento` | date/time | quando aplicável | Data e hora do show conforme programação oficial; não usar como timestamp da observação. |
| `data_referencia` | date/time | sim | Data que a observação representa segundo a fonte (data do ranking/série/publicação). |
| `data_coleta` | datetime com fuso | sim | Timestamp em que o script obteve/processou a resposta. |
| `fuso_coleta` | string | sim | Fuso usado, definido no projeto como America/Sao_Paulo. |
| `metrica` | string | sim | Constructo observado: índice Trends, posição, contagem/listagem etc. |
| `valor` | number/string | quando aplicável | Valor literal/tipado da métrica; não converter Trends em volume absoluto. |
| `unidade` | string | sim | Índice 0–100, posição, presença, contagem de registros etc. |
| `status_observacao` | categoria | sim | `observado`, `provisorio`, `nao_detectado`, `indisponivel`, `nao_coletado`, `n_d` ou zero válido segundo fonte. |
| `motivo_status` | string | quando aplicável | Explica ausência, falha, quota, atraso, Topic não validado ou ausência de baseline. |
| `posicao` | integer | rankings | Posição dentro de lista específica; ausência não implica posição 0. |
| `plataforma_lista` | string | ranking/lista | Lista/chart exato que limita a cobertura (ex.: Spotify Top 200 Brasil). |
| `provisorio` | boolean | sim | Marca observação que ainda pode mudar/reprocessar segundo regra de maturação. |
| `versao_pipeline` | string/commit | sim | Versão de código e tratamento usados na geração. |
| `lote` | string | se batch | Grupo de consulta/execução; necessário para auditar comparabilidade e escala. |
| `http_status` | integer | em erro/resposta | Status da resposta, quando disponível; não publicar conteúdo de cabeçalho que exponha segredo. |
| `tentativa` | integer | em erro/retry | Número da tentativa para a mesma requisição. |
| `latencia_segundos` | number | recomendado | Tempo da requisição ou execução, definido no nível de observação de log, não métrica de artista. |
| `fonte_url` | URL | recomendado | Página ou endpoint de origem permitido para citação; evitar URL temporária/privada. |

## Estados que não podem ser colapsados

| Estado | Significado |
|---|---|
| `zero_valido` | A fonte retornou valor numérico zero na escala própria. |
| `nao_detectado` | Entidade não apareceu na lista limitada verificada. Não significa consumo/uso zero. |
| `nao_coletado` | A tarefa não executou ou não cobriu aquela observação. |
| `indisponivel` | Fonte/endpoint falhou ou não respondeu (ex.: 429). |
| `n_d` | Conceito/linha não tem dado válido (ex.: baseline Nova Twins). |
| `provisorio` | Dado recente ainda sujeito a maturação ou revisão. |
| `observado` | Valor recebido e validado segundo as regras da fonte. |

## Chave e deduplicação

Chave lógica recomendada: `fonte + entidade_id + data_referencia + metrica + plataforma_lista + dimensão`. Se a origem não fornece todos os componentes, documentar a alternativa; não usar somente nome do artista. Registros de execução/log devem ter chave separada da observação científica.
