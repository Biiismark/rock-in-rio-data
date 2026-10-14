from pathlib import Path
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
import re
import unicodedata

import pandas as pd
from unidecode import unidecode


PASTA_PROJETO = (
    Path(__file__).resolve().parents[1]
)

PASTA_REFERENCIAS = (
    PASTA_PROJETO
    / "dados"
    / "referencias"
)

PASTA_BRUTOS = (
    PASTA_PROJETO
    / "dados"
    / "brutos"
    / "paginas_individuais_kworb"
)

PASTA_TRATADOS = (
    PASTA_PROJETO
    / "dados"
    / "tratados"
)

ARQUIVO_MAPEAMENTO = (
    PASTA_REFERENCIAS
    / "mapeamento_paginas_individuais_kworb.csv"
)

ARQUIVO_CHARTS_RIR = (
    PASTA_TRATADOS
    / "charts_brasil_rir_itens.csv"
)

ARQUIVO_SPOTIFY_RIR = (
    PASTA_TRATADOS
    / "spotify_rir_faixas_diario.csv"
)

ARQUIVO_RESULTADO = (
    PASTA_TRATADOS
    / "paginas_individuais_brasil.csv"
)

ARQUIVO_AUDITORIA = (
    PASTA_TRATADOS
    / "auditoria_paginas_individuais_brasil.csv"
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


def converter_movimento(valor):
    valor = limpar_texto(valor)

    if valor == "=":
        return 0

    if re.fullmatch(
        r"[+-]?\d+",
        valor,
    ):
        return int(valor)

    return None


def classificar_plataforma(
    texto_link,
    url,
):
    texto = limpar_texto(
        texto_link
    ).lower()

    url = limpar_texto(
        url
    ).lower()

    if "youtube" in texto or (
        "/youtube/" in url
    ):
        plataforma = "YouTube"

    elif "shazam" in texto or (
        "/shazam/" in url
    ):
        plataforma = "Shazam"

    elif "deezer" in texto or (
        "/deezer/" in url
    ):
        plataforma = "Deezer"

    elif "apple" in texto or (
        "/apple_" in url
    ):
        plataforma = "Apple Music"

    elif "itunes" in texto or (
        "/itunes/" in url
        or "/aitunes/" in url
    ):
        plataforma = "iTunes"

    elif "spotify" in texto or (
        "/spotify/" in url
        or "charts.spotify.com" in url
    ):
        plataforma = "Spotify"

    else:
        plataforma = limpar_texto(
            texto_link
        )

    return plataforma


def classificar_tipo_item(
    texto_link,
    url,
):
    texto = limpar_texto(
        texto_link
    ).lower()

    url = limpar_texto(
        url
    ).lower()

    eh_album = (
        "album" in texto
        or "/apple_a/" in url
        or "/aitunes/" in url
        or "view/album-" in url
    )

    if eh_album:
        return "Álbum"

    if (
        "youtube" in texto
        or "/youtube/" in url
    ):
        return "Música/Vídeo"

    return "Música"


def classificar_periodicidade(
    plataforma,
    tipo_item,
    url,
):
    url = limpar_texto(
        url
    ).lower()

    if (
        "weekly" in url
        or (
            plataforma == "YouTube"
            and "_daily" not in url
        )
    ):
        return "Semanal"

    if (
        "_daily" in url
        or "/country/" in url
    ):
        return "Diária"

    if tipo_item == "Álbum":
        return "Snapshot atual"

    return "Snapshot atual"


def extrair_data_pagina(
    sopa,
):
    texto_pagina = limpar_texto(
        sopa.get_text(
            " ",
            strip=True,
        )
    )

    resultado = re.search(
        r"(\d{4}-\d{2}-\d{2}) "
        r"(\d{2}:\d{2}) "
        r"([A-Z]{2,5})",
        texto_pagina,
    )

    if not resultado:
        return (
            "",
            "",
        )

    data = resultado.group(1)

    horario_fuso = (
        f"{resultado.group(2)} "
        f"{resultado.group(3)}"
    )

    return (
        data,
        horario_fuso,
    )


def encontrar_bloco_brasil(
    sopa,
):
    bloco_paises = sopa.find(
        id="countries"
    )

    if bloco_paises is None:
        return None

    for celula in bloco_paises.find_all(
        "td"
    ):
        primeiro_negrito = celula.find(
            "b"
        )

        if primeiro_negrito is None:
            continue

        pais = limpar_texto(
            primeiro_negrito.get_text(
                " ",
                strip=True,
            )
        )

        if pais == "Brazil":
            return celula

    return None


def extrair_linhas_link(
    link,
):
    linhas = []
    partes_linha = []

    for irmao in link.next_siblings:
        if (
            isinstance(irmao, Tag)
            and irmao.name == "a"
        ):
            break

        if (
            isinstance(irmao, Tag)
            and irmao.name == "br"
        ):
            texto_linha = limpar_texto(
                " ".join(
                    partes_linha
                )
            )

            if texto_linha:
                linhas.append(
                    texto_linha
                )

            partes_linha = []
            continue

        if isinstance(
            irmao,
            NavigableString,
        ):
            texto = limpar_texto(
                str(irmao)
            )

        elif isinstance(
            irmao,
            Tag,
        ):
            texto = limpar_texto(
                irmao.get_text(
                    " ",
                    strip=True,
                )
            )

        else:
            texto = ""

        if texto:
            partes_linha.append(
                texto
            )

    texto_final = limpar_texto(
        " ".join(
            partes_linha
        )
    )

    if texto_final:
        linhas.append(
            texto_final
        )

    return linhas


def interpretar_item(
    texto_linha,
):
    texto = limpar_texto(
        texto_linha
    )

    resultado = re.match(
        r"^(\d+)\.\s+(.+?)"
        r"(?:\s+\(([^()]*)\))?$",
        texto,
    )

    if not resultado:
        return None

    posicao = int(
        resultado.group(1)
    )

    titulo = limpar_texto(
        resultado.group(2)
    )

    movimento = limpar_texto(
        resultado.group(3)
    )

    if not titulo:
        return None

    return {
        "posicao": posicao,
        "titulo": titulo,
        "movimento_24h": movimento,
        "variacao_posicao_24h": (
            converter_movimento(
                movimento
            )
        ),
    }


def extrair_pagina(
    caminho_html,
    artista,
):
    html = caminho_html.read_text(
        encoding="utf-8",
        errors="replace",
    )

    sopa = BeautifulSoup(
        html,
        "lxml",
    )

    (
        data_pagina,
        horario_fuso_pagina,
    ) = extrair_data_pagina(
        sopa
    )

    bloco_brasil = (
        encontrar_bloco_brasil(
            sopa
        )
    )

    if bloco_brasil is None:
        return (
            pd.DataFrame(),
            data_pagina,
            horario_fuso_pagina,
            "sem seção Brasil",
        )

    registros = []

    for link in bloco_brasil.find_all(
        "a",
        href=True,
    ):
        texto_link = limpar_texto(
            link.get_text(
                " ",
                strip=True,
            )
        )

        url_chart = limpar_texto(
            link.get("href")
        )

        plataforma = (
            classificar_plataforma(
                texto_link=texto_link,
                url=url_chart,
            )
        )

        tipo_item = (
            classificar_tipo_item(
                texto_link=texto_link,
                url=url_chart,
            )
        )

        periodicidade = (
            classificar_periodicidade(
                plataforma=plataforma,
                tipo_item=tipo_item,
                url=url_chart,
            )
        )

        linhas = extrair_linhas_link(
            link
        )

        for texto_linha in linhas:
            item = interpretar_item(
                texto_linha
            )

            if item is None:
                continue

            registros.append(
                {
                    "data_pagina": (
                        data_pagina
                    ),
                    "horario_fuso_pagina": (
                        horario_fuso_pagina
                    ),
                    "artista_id": artista[
                        "artista_id"
                    ],
                    "nome_artista": artista[
                        "nome_artista"
                    ],
                    "nome_kworb": artista[
                        "nome_kworb"
                    ],
                    "slug_kworb": artista[
                        "slug_kworb"
                    ],
                    "pais": "Brasil",
                    "plataforma": (
                        plataforma
                    ),
                    "tipo_item": (
                        tipo_item
                    ),
                    "periodicidade": (
                        periodicidade
                    ),
                    "titulo": item[
                        "titulo"
                    ],
                    "titulo_normalizado": (
                        normalizar_texto(
                            item["titulo"]
                        )
                    ),
                    "posicao": item[
                        "posicao"
                    ],
                    "movimento_24h": item[
                        "movimento_24h"
                    ],
                    "variacao_posicao_24h": (
                        item[
                            "variacao_posicao_24h"
                        ]
                    ),
                    "url_chart": (
                        url_chart
                    ),
                    "url_pagina_artista": (
                        artista[
                            "url_pagina_kworb"
                        ]
                    ),
                }
            )

    dados = pd.DataFrame(
        registros
    )

    if dados.empty:
        return (
            dados,
            data_pagina,
            horario_fuso_pagina,
            "Brasil sem itens",
        )

    dados = (
        dados
        .drop_duplicates(
            subset=[
                "artista_id",
                "plataforma",
                "tipo_item",
                "titulo_normalizado",
                "posicao",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return (
        dados,
        data_pagina,
        horario_fuso_pagina,
        "extraído",
    )


def carregar_base_principal():
    registros = []

    if ARQUIVO_CHARTS_RIR.exists():
        charts = pd.read_csv(
            ARQUIVO_CHARTS_RIR,
            encoding="utf-8-sig",
        )

        for _, linha in (
            charts.iterrows()
        ):
            registros.append(
                {
                    "artista_id": linha[
                        "artista_id"
                    ],
                    "plataforma": linha[
                        "plataforma"
                    ],
                    "tipo_item": linha[
                        "tipo_item"
                    ],
                    "titulo_normalizado": (
                        normalizar_texto(
                            linha["titulo"]
                        )
                    ),
                    "posicao_base_principal": (
                        linha["posicao"]
                    ),
                    "data_base_principal": (
                        linha[
                            "data_referencia"
                        ]
                    ),
                    "fonte_base_principal": (
                        linha["fonte"]
                    ),
                }
            )

    if ARQUIVO_SPOTIFY_RIR.exists():
        spotify = pd.read_csv(
            ARQUIVO_SPOTIFY_RIR,
            encoding="utf-8-sig",
        )

        for _, linha in (
            spotify.iterrows()
        ):
            registros.append(
                {
                    "artista_id": linha[
                        "artista_id"
                    ],
                    "plataforma": "Spotify",
                    "tipo_item": "Música",
                    "titulo_normalizado": (
                        normalizar_texto(
                            linha["faixa"]
                        )
                    ),
                    "posicao_base_principal": (
                        linha["posicao"]
                    ),
                    "data_base_principal": (
                        linha[
                            "data_ranking"
                        ]
                    ),
                    "fonte_base_principal": (
                        "spotify_ranking_diario"
                    ),
                }
            )

    if not registros:
        return pd.DataFrame(
            columns=[
                "artista_id",
                "plataforma",
                "tipo_item",
                "titulo_normalizado",
                "posicao_base_principal",
                "data_base_principal",
                "fonte_base_principal",
            ]
        )

    base = pd.DataFrame(
        registros
    )

    base = (
        base
        .drop_duplicates(
            subset=[
                "artista_id",
                "plataforma",
                "tipo_item",
                "titulo_normalizado",
            ],
            keep="last",
        )
        .reset_index(
            drop=True
        )
    )

    return base


def comparar_com_base(
    itens,
    base,
):
    chaves = [
        "artista_id",
        "plataforma",
        "tipo_item",
        "titulo_normalizado",
    ]

    resultado = itens.merge(
        base,
        on=chaves,
        how="left",
        validate="many_to_one",
    )

    resultado[
        "encontrado_base_principal"
    ] = resultado[
        "fonte_base_principal"
    ].notna()

    resultado[
        "item_adicional_pagina_individual"
    ] = ~resultado[
        "encontrado_base_principal"
    ]

    resultado[
        "diferenca_posicao"
    ] = (
        resultado["posicao"]
        - resultado[
            "posicao_base_principal"
        ]
    )

    return resultado


def main():
    print(
        "EXTRAINDO POSIÇÕES DO BRASIL "
        "DAS PÁGINAS INDIVIDUAIS"
    )

    if not ARQUIVO_MAPEAMENTO.exists():
        print(
            f"\nERRO: arquivo não encontrado: "
            f"{ARQUIVO_MAPEAMENTO}"
        )

        return

    mapeamento = pd.read_csv(
        ARQUIVO_MAPEAMENTO,
        encoding="utf-8-sig",
        dtype=str,
    ).fillna("")

    paginas_baixadas = mapeamento[
        mapeamento[
            "status_download"
        ].eq(
            "baixado"
        )
    ]

    todos_itens = []
    auditoria = []

    total = len(
        paginas_baixadas
    )

    for numero, (_, artista) in enumerate(
        paginas_baixadas.iterrows(),
        start=1,
    ):
        slug = artista[
            "slug_kworb"
        ]

        caminho_html = (
            PASTA_BRUTOS
            / f"{slug}.html"
        )

        print(
            f"[{numero}/{total}] "
            f"{artista['nome_artista']}"
        )

        if not caminho_html.exists():
            print(
                "   HTML não encontrado"
            )

            auditoria.append(
                {
                    "artista_id": artista[
                        "artista_id"
                    ],
                    "nome_artista": artista[
                        "nome_artista"
                    ],
                    "status_extracao": (
                        "HTML não encontrado"
                    ),
                    "data_pagina": "",
                    "quantidade_itens_brasil": 0,
                }
            )

            continue

        (
            dados,
            data_pagina,
            horario_fuso_pagina,
            status,
        ) = extrair_pagina(
            caminho_html=caminho_html,
            artista=artista,
        )

        quantidade = len(
            dados
        )

        print(
            f"   Status: {status} | "
            f"Itens Brasil: {quantidade}"
        )

        if not dados.empty:
            todos_itens.append(
                dados
            )

        auditoria.append(
            {
                "artista_id": artista[
                    "artista_id"
                ],
                "nome_artista": artista[
                    "nome_artista"
                ],
                "status_extracao": status,
                "data_pagina": (
                    data_pagina
                ),
                "horario_fuso_pagina": (
                    horario_fuso_pagina
                ),
                "quantidade_itens_brasil": (
                    quantidade
                ),
            }
        )

    if todos_itens:
        itens = pd.concat(
            todos_itens,
            ignore_index=True,
        )

    else:
        itens = pd.DataFrame()

    auditoria = pd.DataFrame(
        auditoria
    )

    if itens.empty:
        resultado = itens

    else:
        base = carregar_base_principal()

        resultado = comparar_com_base(
            itens=itens,
            base=base,
        )

        resultado = (
            resultado
            .sort_values(
                [
                    "nome_artista",
                    "plataforma",
                    "tipo_item",
                    "posicao",
                ]
            )
            .reset_index(
                drop=True
            )
        )

    resultado.to_csv(
        ARQUIVO_RESULTADO,
        index=False,
        encoding="utf-8-sig",
    )

    auditoria.to_csv(
        ARQUIVO_AUDITORIA,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        "\nEXTRAÇÃO CONCLUÍDA"
    )

    print(
        f"Páginas analisadas: "
        f"{len(auditoria)}"
    )

    print(
        f"Itens brasileiros encontrados: "
        f"{len(resultado)}"
    )

    if not resultado.empty:
        print(
            "Artistas com itens no Brasil: "
            f"{resultado['artista_id'].nunique()}"
        )

        confirmados = int(
            resultado[
                "encontrado_base_principal"
            ].sum()
        )

        adicionais = int(
            resultado[
                "item_adicional_pagina_individual"
            ].sum()
        )

        print(
            f"Itens confirmados na base principal: "
            f"{confirmados}"
        )

        print(
            "Itens adicionais das páginas "
            f"individuais: {adicionais}"
        )

        print(
            "\nResumo:"
        )

        resumo = (
            resultado
            .groupby(
                [
                    "plataforma",
                    "tipo_item",
                    "nome_artista",
                ],
                as_index=False,
            )
            .agg(
                quantidade=(
                    "titulo_normalizado",
                    "nunique",
                ),
                melhor_posicao=(
                    "posicao",
                    "min",
                ),
            )
        )

        print(
            resumo.to_string(
                index=False
            )
        )

    print(
        f"\nResultado salvo em: "
        f"{ARQUIVO_RESULTADO}"
    )

    print(
        f"Auditoria salva em: "
        f"{ARQUIVO_AUDITORIA}"
    )

    print(
        "\nAs páginas individuais são uma "
        "camada complementar. Quando a data "
        "for diferente da base principal, a "
        "posição não deve ser tratada como "
        "divergência de coleta."
    )


if __name__ == "__main__":
    main()