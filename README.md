# Rock in Rio 2026 — pacote de avaliação e reprodutibilidade

Pacote público complementar do artigo tecnológico submetido à Revista IPTEC. O objeto do artigo é o **ferramental de coleta, integração, validação e publicação de indicadores digitais**. As observações sobre artistas servem para demonstrar cobertura e funcionamento; não são usadas para testar se um artista “cresceu” nem para atribuir efeito causal ao festival.

## Conteúdo

- [Escopo e matriz técnica de questionamentos](docs/matriz-tecnica.md)
- [Registro de falhas, correções e limitações](docs/falhas-e-solucoes.md)
- [Protocolo de coleta e tratamento](docs/protocolo.md)
- [Dicionário de dados](docs/dicionario-de-dados.md)
- [Fontes e proveniência](docs/fontes-e-proveniencia.md)
- [Referências teóricas e técnicas](docs/referencias.md)
- [Código selecionado](scripts/)

## Recorte congelado

A evidência principal foi congelada em **28/09/2026** (fuso America/Sao_Paulo). Observações posteriores são complementares e não sobrescrevem o corte científico. O relatório de auditoria registra 28 artistas, 7 dias e 112/112 checkpoints consolidados para Google Trends V2 em D0, D+1, D+3 e D+7; 7.980 observações Trends consolidadas até 23/09 e 60 observações provisórias de 24–25/09. N/D, provisório e não detectado permanecem estados distintos de zero.

## Reprodutibilidade e limites de redistribuição

Este repositório publica documentação, esquemas e código selecionado; **não redistribui snapshots integrais de plataformas, páginas HTML, imagens, artigos jornalísticos ou conteúdo protegido**. Para reproduzir a coleta, o pesquisador deve consultar as fontes originais, observar os termos vigentes e registrar data/hora, parâmetros, versão do código e disponibilidade. Acesso ao banco de produção não é necessário nem fornecido por este pacote.

Nenhuma chave ou credencial deve ser armazenada aqui. Variáveis de ambiente e credenciais de serviço são omitidas. O código que grava no Supabase requer configuração própria do pesquisador e schema compatível. A execução reproduz o procedimento, mas pode não recuperar exatamente a mesma resposta, pois plataformas e bibliotecas podem mudar.

## Organização do projeto

| Pasta | Conteúdo |
|---|---|
| `docs/` | protocolo, inventário, matriz técnica, falhas e referências |
| `scripts/` | código selecionado para demonstrar extração/controle |
| `data/` | reservado a manifests e dados redistribuíveis após revisão de direitos |

## Citação

Aguiar, B. (2026). *Rock in Rio 2026: pacote de avaliação e reprodutibilidade do ferramental de monitoramento digital* [Repositório de código e documentação]. GitHub. https://github.com/Biiismark/rock-in-rio-data

O artigo e este pacote devem ser citados separadamente. Este repositório ainda não tem DOI. Para submissão, recomenda-se arquivar uma versão imutável em Zenodo e inserir o DOI quando o pacote estiver finalizado.

## Estado editorial

Pacote inicial organizado para auditoria. A matriz técnica e o registro de falhas foram sintetizados dos documentos de projeto e dos relatórios de auditoria; antes de submissão, confira-os contra a versão final dos dados e acrescente hash/commit do snapshot que será citado.
