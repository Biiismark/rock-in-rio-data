from hashlib import sha1
from pathlib import Path
from difflib import SequenceMatcher
import re
import unicodedata

import pandas as pd
from unidecode import unidecode


PASTA_PROJETO = (
    Path(__file__).resolve().parents[1]
)

PASTA_TRATADOS = (
    PASTA_PROJETO
    / "dados"
    / "tratados"
)

ARQUIVO_CHARTS = (
    PASTA_TRATADOS
    / "charts_brasil_rir_itens.csv"
)

ARQUIVO_SPOTIFY = (
    PASTA_TRATADOS
    / "spotify_rir_faixas_diario.csv"
)

ARQUIVO_PAGINAS = (
    PASTA_TRATADOS
    / "paginas_individuais_brasil.csv"
)

ARQUIVO_CONSOLIDADO = (
    PASTA_TRATADOS
    / "presenca_atual_rir_consolidada.csv"
)

ARQUIVO_AUDITORIA = (
    PASTA_TRATADOS
    / "auditoria_consolidacao_paginas.csv"
)


def limpar_texto(valor):
    if valor is None or pd.isna(valor):
        return ""

    texto = unicodedata.normalize(
        "NFKC",
        str(valor),
    )

    texto = re.sub(
        r"[\u200b\u200c\u200d\ufeff]",
        "",
        texto,
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto.strip()


def normalizar_texto(valor):
    texto = limpar_texto(valor)
    texto = unidecode(texto).lower()

    texto = re.sub(
        r"[^a-z0-9]+",
        "_",
        texto,
    )

    return texto.strip("_")


def normalizar_titulo_comparacao(
    titulo,
    nome_artista="",
):
    titulo = limpar_texto(
        titulo
    )

    nome_artista = limpar_texto(
        nome_artista
    )

    titulo = re.sub(
        r"\([^)]*\)",
        " ",
        titulo,
    )

    titulo = re.sub(
        r"\[[^\]]*\]",
        " ",
        titulo,
    )

    titulo = re.sub(
        r"\b("
        r"remaster|remastered|"
        r"deluxe|edition|version|"
        r"live|ao vivo|"
        r"little bit extra"
        r")\b",
        " ",
        titulo,
        flags=re.IGNORECASE,
    )

    if nome_artista:
        titulo = re.sub(
            rf"^\s*{re.escape(nome_artista)}"
            r"\s*[-–—:]\s*",
            "",
            titulo,
            flags=re.IGNORECASE,
        )

    return normalizar_texto(
        titulo
    )


def similaridade(
    titulo_a,
    titulo_b,
):
    if not titulo_a or not titulo_b:
        return 0.0

    if (
        titulo_a in titulo_b
        or titulo_b in titulo_a
    ):
        return 1.0

    return SequenceMatcher(
        None,
        titulo_a,
        titulo_b,
    ).ratio()


def criar_registro_id(
    origem,
    data_referencia,
    artista_id,
    plataforma,
    tipo_item,
    titulo,
    posicao,
):
    base = "|".join(
        [
            normalizar_texto(
                origem
            ),
            limpar_texto(
                data_referencia
            ),
            limpar_texto(
                artista_id
            ),
            normalizar_texto(
                plataforma
            ),
            normalizar_texto(
                tipo_item
            ),
            normalizar_texto(
                titulo
            ),
            limpar_texto(
                posicao
            ),
        ]
    )

    return sha1(
        base.encode("utf-8")
    ).hexdigest()[:20]


def carregar_csv(
    caminho,
    nome,
):
    if not caminho.exists():
        raise FileNotFoundError(
            f"{nome} não encontrado: "
            f"{caminho}"
        )

    return pd.read_csv(
        caminho,
        encoding="utf-8-sig",
    )


def preparar_charts(
    charts,
):
    registros = []

    for _, linha in (
        charts.iterrows()
    ):
        plataforma = limpar_texto(
            linha["plataforma"]
        )

        valor = linha.get(
            "valor_fonte"
        )

        if (
            plataforma == "YouTube"
            and pd.notna(valor)
        ):
            tipo_valor = (
                "Visualizações da fonte"
            )

        elif pd.notna(valor):
            tipo_valor = (
                "Valor informado pela fonte"
            )

        else:
            tipo_valor = ""

        registro = {
            "data_referencia": limpar_texto(
                linha["data_referencia"]
            ),
            "tipo_data": limpar_texto(
                linha.get("tipo_data")
            ),
            "artista_id": limpar_texto(
                linha["artista_id"]
            ),
            "nome_artista": limpar_texto(
                linha["nome_artista"]
            ),
            "plataforma": plataforma,
            "tipo_item": limpar_texto(
                linha["tipo_item"]
            ),
            "periodicidade": limpar_texto(
                linha["periodicidade"]
            ),
            "titulo": limpar_texto(
                linha["titulo"]
            ),
            "posicao": linha["posicao"],
            "movimento_posicao": limpar_texto(
                linha.get(
                    "movimento_posicao"
                )
            ),
            "valor": valor,
            "tipo_valor": tipo_valor,
            "fonte": limpar_texto(
                linha["fonte"]
            ),
            "origem_registro": (
                "chart nacional direto"
            ),
            "prioridade_fonte": 1,
            "data_plataforma_confirmada": True,
            "url_fonte": limpar_texto(
                linha.get("url_fonte")
            ),
        }

        registros.append(
            registro
        )

    return pd.DataFrame(
        registros
    )


def preparar_spotify(
    spotify,
):
    registros = []

    for _, linha in (
        spotify.iterrows()
    ):
        registros.append(
            {
                "data_referencia": (
                    limpar_texto(
                        linha[
                            "data_ranking"
                        ]
                    )
                ),
                "tipo_data": (
                    "Data publicada pela fonte"
                ),
                "artista_id": limpar_texto(
                    linha["artista_id"]
                ),
                "nome_artista": limpar_texto(
                    linha["nome_artista"]
                ),
                "plataforma": "Spotify",
                "tipo_item": "Música",
                "periodicidade": "Diária",
                "titulo": limpar_texto(
                    linha["faixa"]
                ),
                "posicao": linha[
                    "posicao"
                ],
                "movimento_posicao": (
                    limpar_texto(
                        linha.get(
                            "movimento_posicao"
                        )
                    )
                ),
                "valor": linha.get(
                    "streams_dia"
                ),
                "tipo_valor": (
                    "Streams no dia"
                ),
                "fonte": (
                    "spotify_ranking_diario"
                ),
                "origem_registro": (
                    "chart nacional direto"
                ),
                "prioridade_fonte": 1,
                "data_plataforma_confirmada": (
                    True
                ),
                "url_fonte": limpar_texto(
                    linha.get("url_fonte")
                ),
            }
        )

    return pd.DataFrame(
        registros
    )


def preparar_base_direta(
    charts,
    spotify,
):
    base = pd.concat(
        [
            preparar_charts(
                charts
            ),
            preparar_spotify(
                spotify
            ),
        ],
        ignore_index=True,
    )

    base[
        "titulo_normalizado"
    ] = base[
        "titulo"
    ].map(
        normalizar_texto
    )

    base[
        "titulo_comparacao"
    ] = base.apply(
        lambda linha: (
            normalizar_titulo_comparacao(
                linha["titulo"],
                linha["nome_artista"],
            )
        ),
        axis=1,
    )

    base[
        "registro_id"
    ] = base.apply(
        lambda linha: criar_registro_id(
            origem=linha[
                "origem_registro"
            ],
            data_referencia=linha[
                "data_referencia"
            ],
            artista_id=linha[
                "artista_id"
            ],
            plataforma=linha[
                "plataforma"
            ],
            tipo_item=linha[
                "tipo_item"
            ],
            titulo=linha[
                "titulo"
            ],
            posicao=linha[
                "posicao"
            ],
        ),
        axis=1,
    )

    base = (
        base
        .drop_duplicates(
            subset=[
                "registro_id",
            ],
            keep="last",
        )
        .reset_index(
            drop=True
        )
    )

    return base


def escolher_correspondencia(
    pagina,
    candidatos,
):
    if candidatos.empty:
        return (
            None,
            "complemento real",
            0.0,
        )

    exatos = candidatos[
        candidatos[
            "titulo_normalizado"
        ].eq(
            pagina[
                "titulo_normalizado"
            ]
        )
    ]

    if not exatos.empty:
        mesma_posicao = exatos[
            exatos[
                "posicao"
            ].eq(
                pagina["posicao"]
            )
        ]

        escolhido = (
            mesma_posicao.iloc[-1]
            if not mesma_posicao.empty
            else exatos.iloc[-1]
        )

        return (
            escolhido,
            "correspondência exata",
            1.0,
        )

    melhor_linha = None
    melhor_similaridade = 0.0

    for _, candidato in (
        candidatos.iterrows()
    ):
        pontuacao = similaridade(
            pagina[
                "titulo_comparacao"
            ],
            candidato[
                "titulo_comparacao"
            ],
        )

        mesma_posicao = (
            int(candidato["posicao"])
            == int(pagina["posicao"])
        )

        if (
            mesma_posicao
            and pontuacao
            > melhor_similaridade
        ):
            melhor_linha = candidato
            melhor_similaridade = (
                pontuacao
            )

    if (
        melhor_linha is not None
        and melhor_similaridade >= 0.50
    ):
        return (
            melhor_linha,
            "mesmo item com título variado",
            melhor_similaridade,
        )

    return (
        None,
        "complemento real",
        melhor_similaridade,
    )


def auditar_paginas(
    paginas,
    base_direta,
):
    auditoria = []
    complementos = []

    paginas = paginas.copy()

    paginas[
        "titulo_normalizado"
    ] = paginas[
        "titulo"
    ].map(
        normalizar_texto
    )

    paginas[
        "titulo_comparacao"
    ] = paginas.apply(
        lambda linha: (
            normalizar_titulo_comparacao(
                linha["titulo"],
                linha["nome_artista"],
            )
        ),
        axis=1,
    )

    for _, pagina in (
        paginas.iterrows()
    ):
        candidatos = base_direta[
            (
                base_direta[
                    "artista_id"
                ].eq(
                    pagina[
                        "artista_id"
                    ]
                )
            )
            & (
                base_direta[
                    "plataforma"
                ].eq(
                    pagina[
                        "plataforma"
                    ]
                )
            )
            & (
                base_direta[
                    "tipo_item"
                ].eq(
                    pagina[
                        "tipo_item"
                    ]
                )
            )
        ]

        (
            correspondencia,
            classificacao,
            pontuacao,
        ) = escolher_correspondencia(
            pagina=pagina,
            candidatos=candidatos,
        )

        if correspondencia is None:
            titulo_base = ""
            posicao_base = None
            data_base = ""
            fonte_base = ""

        else:
            titulo_base = correspondencia[
                "titulo"
            ]

            posicao_base = correspondencia[
                "posicao"
            ]

            data_base = correspondencia[
                "data_referencia"
            ]

            fonte_base = correspondencia[
                "fonte"
            ]

        auditoria.append(
            {
                "artista_id": pagina[
                    "artista_id"
                ],
                "nome_artista": pagina[
                    "nome_artista"
                ],
                "plataforma": pagina[
                    "plataforma"
                ],
                "tipo_item": pagina[
                    "tipo_item"
                ],
                "titulo_pagina": pagina[
                    "titulo"
                ],
                "posicao_pagina": pagina[
                    "posicao"
                ],
                "data_observacao_pagina": (
                    pagina[
                        "data_pagina"
                    ]
                ),
                "classificacao": (
                    classificacao
                ),
                "similaridade_titulo": round(
                    pontuacao,
                    4,
                ),
                "titulo_base_direta": (
                    titulo_base
                ),
                "posicao_base_direta": (
                    posicao_base
                ),
                "data_base_direta": (
                    data_base
                ),
                "fonte_base_direta": (
                    fonte_base
                ),
            }
        )

        if classificacao == (
            "complemento real"
        ):
            complemento = {
                "data_referencia": (
                    limpar_texto(
                        pagina[
                            "data_pagina"
                        ]
                    )
                ),
                "tipo_data": (
                    "Momento da página agregadora; "
                    "data própria da plataforma "
                    "não informada"
                ),
                "artista_id": limpar_texto(
                    pagina[
                        "artista_id"
                    ]
                ),
                "nome_artista": limpar_texto(
                    pagina[
                        "nome_artista"
                    ]
                ),
                "plataforma": limpar_texto(
                    pagina[
                        "plataforma"
                    ]
                ),
                "tipo_item": limpar_texto(
                    pagina[
                        "tipo_item"
                    ]
                ),
                "periodicidade": (
                    "Snapshot complementar"
                ),
                "titulo": limpar_texto(
                    pagina["titulo"]
                ),
                "posicao": pagina[
                    "posicao"
                ],
                "movimento_posicao": (
                    limpar_texto(
                        pagina.get(
                            "movimento_24h"
                        )
                    )
                ),
                "valor": None,
                "tipo_valor": "",
                "fonte": (
                    "pagina_individual_kworb"
                ),
                "origem_registro": (
                    "complemento da página "
                    "individual"
                ),
                "prioridade_fonte": 2,
                "data_plataforma_confirmada": (
                    False
                ),
                "url_fonte": limpar_texto(
                    pagina.get(
                        "url_pagina_artista"
                    )
                ),
                "titulo_normalizado": (
                    pagina[
                        "titulo_normalizado"
                    ]
                ),
                "titulo_comparacao": (
                    pagina[
                        "titulo_comparacao"
                    ]
                ),
            }

            complemento[
                "registro_id"
            ] = criar_registro_id(
                origem=complemento[
                    "origem_registro"
                ],
                data_referencia=complemento[
                    "data_referencia"
                ],
                artista_id=complemento[
                    "artista_id"
                ],
                plataforma=complemento[
                    "plataforma"
                ],
                tipo_item=complemento[
                    "tipo_item"
                ],
                titulo=complemento[
                    "titulo"
                ],
                posicao=complemento[
                    "posicao"
                ],
            )

            complementos.append(
                complemento
            )

    return (
        pd.DataFrame(
            auditoria
        ),
        pd.DataFrame(
            complementos
        ),
    )


def criar_consolidado(
    base_direta,
    complementos,
):
    if complementos.empty:
        resultado = (
            base_direta.copy()
        )

    else:
        resultado = pd.concat(
            [
                base_direta,
                complementos,
            ],
            ignore_index=True,
        )

    resultado = (
        resultado
        .drop_duplicates(
            subset=[
                "registro_id",
            ],
            keep="last",
        )
        .sort_values(
            [
                "data_referencia",
                "plataforma",
                "tipo_item",
                "nome_artista",
                "posicao",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return resultado


def main():
    print(
        "CONSOLIDANDO PRESENÇA ATUAL "
        "DOS ARTISTAS DO ROCK IN RIO"
    )

    try:
        charts = carregar_csv(
            ARQUIVO_CHARTS,
            "Charts brasileiros",
        )

        spotify = carregar_csv(
            ARQUIVO_SPOTIFY,
            "Spotify diário",
        )

        paginas = carregar_csv(
            ARQUIVO_PAGINAS,
            "Páginas individuais",
        )

        base_direta = preparar_base_direta(
            charts=charts,
            spotify=spotify,
        )

        (
            auditoria,
            complementos,
        ) = auditar_paginas(
            paginas=paginas,
            base_direta=base_direta,
        )

        consolidado = criar_consolidado(
            base_direta=base_direta,
            complementos=complementos,
        )

    except (
        FileNotFoundError,
        ValueError,
    ) as erro:
        print(
            f"\nERRO: {erro}"
        )

        return

    consolidado.to_csv(
        ARQUIVO_CONSOLIDADO,
        index=False,
        encoding="utf-8-sig",
    )

    auditoria.to_csv(
        ARQUIVO_AUDITORIA,
        index=False,
        encoding="utf-8-sig",
    )

    resumo_auditoria = (
        auditoria[
            "classificacao"
        ].value_counts()
    )

    print(
        "\nCONSOLIDAÇÃO CONCLUÍDA"
    )

    print(
        f"Registros diretos: "
        f"{len(base_direta)}"
    )

    print(
        f"Complementos reais: "
        f"{len(complementos)}"
    )

    print(
        f"Registros consolidados: "
        f"{len(consolidado)}"
    )

    print(
        "\nAuditoria das páginas:"
    )

    for classificacao, quantidade in (
        resumo_auditoria.items()
    ):
        print(
            f" - {classificacao}: "
            f"{quantidade}"
        )

    print(
        f"\nBase consolidada: "
        f"{ARQUIVO_CONSOLIDADO}"
    )

    print(
        f"Auditoria: "
        f"{ARQUIVO_AUDITORIA}"
    )

    print(
        "\nRegistros com "
        "data_plataforma_confirmada=False "
        "não devem alimentar gráficos de "
        "evolução diária."
    )


if __name__ == "__main__":
    main()