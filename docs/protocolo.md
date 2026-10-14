# Protocolo resumido de coleta e tratamento

## Finalidade do artefato

Construir um fluxo automatizado e auditável para observar sinais públicos relacionados ao Rock in Rio 2026, integrá-los por fonte e disponibilizar consultas/relatórios com limites explícitos. Este protocolo é do artigo ferramental. Não define inferência causal sobre o festival.

## Unidade, escopo e corte

- Universo de configuração: 28 apresentações/artistas do Palco Mundo; mais entidades contextuais (evento e marca) apenas quando pertinentes à fonte.
- Território: Brasil (Google Trends geo=BR; demais fontes conforme ranking nacional).
- Janela principal: baseline pré-festival e observações em torno das apresentações, com checkpoints D0, D+1, D+3 e D+7.
- Freeze científico: 28/09/2026, America/Sao_Paulo.
- Atualizações posteriores: camada operacional/complementar; nunca sobrescreve silenciosamente o corte.
- Google Trends V2: 30 entidades; série individual por Topic/MID, sem comparação de índice bruto entre entidades. Dados até 23/09 consolidados; 24–25/09 provisórios no freeze.
- Dados ausentes, fora da lista, indisponíveis, provisórios e zeros da própria plataforma são categorias diferentes.

## Três tempos

Cada observação preserva (quando disponível) (1) data/hora do show ou evento, (2) data de referência/publicação da fonte, (3) timestamp da coleta e fuso. A classificação de D relativo usa a data de referência publicada pela fonte; o horário de execução não transforma dado atrasado em observação atual.

## Fontes, coleta e periodicidade

Consultar `fontes-e-proveniencia.md` e `dicionario-de-dados.md`. A periodicidade deve seguir o limite e a latência efetiva de cada serviço. Trends usa pausas de 65–85 s entre chamadas e 300 s após 429, com retentativa limitada. A chamada de related queries pode permanecer indisponível; não substitui a série principal de interesse.

## Tratamento

1. Manter identificador estável da entidade e guardar nome/alias usado na consulta.
2. Preservar dado de origem e metadados de coleta sempre que redistribuição/licença permitir; quando não permitir, publicar apenas esquema, agregados permitidos e instruções de reconsulta.
3. Padronizar fuso para America/Sao_Paulo e manter timestamp original da fonte.
4. Não preencher ausências com zero; aplicar status explícito.
5. Deduplicar por chave composta documentada (fonte + entidade + data de referência + métrica + dimensão), guardar contagem/relatório de alteração.
6. Separar dados recentes não maturados como provisórios.
7. Calcular cobertura, min/max, chaves, duplicidades e estado de cada fonte antes de liberar snapshot.
8. Congelar código e dados por commit/hash; correções tardias entram em adendo.
9. Não somar contagens de listas diferentes como se fossem uma mesma métrica.
10. Trends é índice relativo; ranking é presença censurada; TikTok é lista monitorada/circulação, não consumo total.

## Avaliação do artefato

Reportar denominadores e métodos para: cobertura prevista vs observada; execução bem-sucedida; falhas por fonte; retries; atraso/frescor; duplicidades; reconciliação GitHub/Supabase; consistência entre execução independente e saída; facilidade de reproduzir; utilidade para analista. Resultado do congelamento: 112/112 pontos primários de Trends D0/D+1/D+3/D+7 consolidados; Actions #40 sucesso (27/09); status de integridade registrado OK no freeze. A redução da taxa de HTTP 429 com os intervalos maiores ainda não foi quantificada.

## Execução pública

O pacote não fornece credenciais nem acesso ao Supabase de produção. Para reprodução:
1. usar Python 3.12 e dependências especificadas em `requirements.txt` (arquivo mínimo a finalizar);
2. obter dados novamente das fontes, respeitando termos e cotas atuais;
3. configurar credenciais próprias somente como variáveis de ambiente, se optar por armazenamento Supabase;
4. registrar timestamp, fuso, parâmetros, respostas de erro, versões e commit;
5. executar validações e comparar manifests; não esperar respostas idênticas às de 2026, pois são dados dinâmicos.

## Privacidade e direitos

Não incluir conteúdo editorial integral, HTML, imagens, perfis pessoais, chaves, tokens, service-role keys ou export bruto de terceiros sem verificar direito de redistribuição. A fonte pública e o método devem ser citados; acesso aberto à página não concede licença para republicar seu conteúdo.
