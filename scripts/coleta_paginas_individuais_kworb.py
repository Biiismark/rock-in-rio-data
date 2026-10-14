from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import re
import time
import unicodedata

import pandas as pd
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode


URLS_INDICES = {
    "ranking_principal": (
        "https://kworb.net/itunes/"
    ),
    "ranking_estendido": (
        "https://kworb.net/itunes/"
        "extended.html"
    ),
}

URL_PAGINA_ARTISTA = (
    "https://kworb.net/itunes/artist/"
    "{slug}.html"
)

CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
}

FUSO_BRASIL = ZoneInfo(
    "America/Sao_Paulo"
)

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

ARQUIVO_MAPEAMENTO = (
    PASTA_REFERENCIAS
    / "mapeamento_artistas_spotify.csv"
)

ARQUIVO_PAGINAS = (
    PASTA_REFERENCIAS
    / "mapeamento_paginas_individuais_kworb.csv"
)

PASTA_BRUTOS.mkdir(
    parents=True,
    exist_ok=True,
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


def baixar_pagina(
    sessao,
    url,
):
    resposta = sessao.get(
        url,
        headers=CABECALHOS,
        timeout=60,
    )

    resposta.raise_for_status()
    resposta.encoding = "utf-8"

    return resposta.text


def extrair_catalogo_indice(
    html,
    nome_indice,
):
    sopa = BeautifulSoup(
        html,
        "lxml",
    )

    registros = []

    padrao_link = re.compile(
        r"(?:/itunes/)?"
        r"artist/"
        r"([^/?#]+)"
        r"\.html"
        r"(?:[?#].*)?$"
    )

    for link in sopa.find_all(
        "a",
        href=True,
    ):
        href = limpar_texto(
            link.get("href")
        )

        resultado = padrao_link.search(
            href
        )

        if not resultado:
            continue

        slug = limpar_texto(
            resultado.group(1)
        )

        nome_kworb = limpar_texto(
            link.get_text(
                " ",
                strip=True,
            )
        )

        if not slug or not nome_kworb:
            continue

        registros.append(
            {
                "nome_kworb": nome_kworb,
                "nome_kworb_normalizado": (
                    normalizar_texto(
                        nome_kworb
                    )
                ),
                "slug_kworb": slug,
                "indice_origem": nome_indice,
                "url_pagina": (
                    URL_PAGINA_ARTISTA.format(
                        slug=slug
                    )
                ),
            }
        )

    return registros


def construir_catalogo(
    sessao,
):
    registros = []

    for (
        nome_indice,
        url,
    ) in URLS_INDICES.items():
        print(
            f"Coletando índice: "
            f"{nome_indice}..."
        )

        html = baixar_pagina(
            sessao=sessao,
            url=url,
        )

        arquivo_html = (
            PASTA_BRUTOS
            / f"{nome_indice}.html"
        )

        arquivo_html.write_text(
            html,
            encoding="utf-8",
        )

        encontrados = (
            extrair_catalogo_indice(
                html=html,
                nome_indice=nome_indice,
            )
        )

        registros.extend(
            encontrados
        )

        print(
            f"   Links encontrados: "
            f"{len(encontrados)}"
        )

    if not registros:
        raise ValueError(
            "Nenhuma página individual "
            "foi encontrada nos índices."
        )

    catalogo = pd.DataFrame(
        registros
    )

    catalogo = (
        catalogo
        .drop_duplicates(
            subset=[
                "nome_kworb_normalizado",
                "slug_kworb",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return catalogo


def criar_nomes_procurados(
    linha,
):
    candidatos = {
        limpar_texto(
            linha.get(
                "nome_spotify_esperado"
            )
        ),
        limpar_texto(
            linha.get(
                "spotify_nome_artista"
            )
        ),
    }

    return {
        normalizar_texto(nome)
        for nome in candidatos
        if normalizar_texto(nome)
    }


def mapear_paginas(
    mapeamento,
    catalogo,
):
    registros = []

    for _, linha in (
        mapeamento.iterrows()
    ):
        artista_id = limpar_texto(
            linha["artista_id"]
        )

        nome_artista = limpar_texto(
            linha["nome_artista"]
        )

        nomes_procurados = (
            criar_nomes_procurados(
                linha
            )
        )

        candidatos = catalogo[
            catalogo[
                "nome_kworb_normalizado"
            ].isin(
                nomes_procurados
            )
        ].copy()

        slugs = sorted(
            candidatos[
                "slug_kworb"
            ]
            .dropna()
            .unique()
            .tolist()
        )

        if len(slugs) == 0:
            status = "não encontrado"
            slug = ""
            nome_kworb = ""
            url_pagina = ""

        elif len(slugs) == 1:
            status = "encontrado"
            slug = slugs[0]

            correspondente = candidatos[
                candidatos[
                    "slug_kworb"
                ].eq(
                    slug
                )
            ].iloc[0]

            nome_kworb = (
                correspondente[
                    "nome_kworb"
                ]
            )

            url_pagina = (
                correspondente[
                    "url_pagina"
                ]
            )

        else:
            status = "ambíguo"
            slug = " | ".join(
                slugs
            )

            nome_kworb = " | ".join(
                sorted(
                    candidatos[
                        "nome_kworb"
                    ]
                    .dropna()
                    .unique()
                    .tolist()
                )
            )

            url_pagina = ""

        registros.append(
            {
                "artista_id": artista_id,
                "nome_artista": nome_artista,
                "spotify_nome_artista": (
                    limpar_texto(
                        linha.get(
                            "spotify_nome_artista"
                        )
                    )
                ),
                "status_pagina_kworb": (
                    status
                ),
                "nome_kworb": nome_kworb,
                "slug_kworb": slug,
                "url_pagina_kworb": (
                    url_pagina
                ),
            }
        )

    return pd.DataFrame(
        registros
    )


def baixar_paginas_artistas(
    sessao,
    paginas,
):
    agora = datetime.now(
        FUSO_BRASIL
    ).isoformat(
        timespec="seconds"
    )

    paginas = paginas.copy()

    paginas[
        "status_download"
    ] = "não aplicável"

    paginas[
        "arquivo_html"
    ] = ""

    paginas[
        "coletado_em"
    ] = ""

    paginas[
        "erro_download"
    ] = ""

    encontrados = paginas[
        paginas[
            "status_pagina_kworb"
        ].eq(
            "encontrado"
        )
    ]

    total = len(
        encontrados
    )

    for numero, indice in enumerate(
        encontrados.index,
        start=1,
    ):
        linha = paginas.loc[
            indice
        ]

        nome_artista = linha[
            "nome_artista"
        ]

        slug = linha[
            "slug_kworb"
        ]

        url = linha[
            "url_pagina_kworb"
        ]

        print(
            f"[{numero}/{total}] "
            f"{nome_artista}"
        )

        try:
            html = baixar_pagina(
                sessao=sessao,
                url=url,
            )

            caminho_html = (
                PASTA_BRUTOS
                / f"{slug}.html"
            )

            caminho_html.write_text(
                html,
                encoding="utf-8",
            )

            paginas.at[
                indice,
                "status_download",
            ] = "baixado"

            paginas.at[
                indice,
                "arquivo_html",
            ] = str(
                caminho_html
            )

            paginas.at[
                indice,
                "coletado_em",
            ] = agora

            print(
                "   Página salva"
            )

        except requests.RequestException as erro:
            paginas.at[
                indice,
                "status_download",
            ] = "erro"

            paginas.at[
                indice,
                "erro_download",
            ] = str(
                erro
            )

            print(
                f"   ERRO: {erro}"
            )

        time.sleep(
            0.25
        )

    return paginas


def validar_resultado(
    mapeamento,
    paginas,
):
    if len(paginas) != len(mapeamento):
        raise ValueError(
            "O resultado não possui uma "
            "linha para cada artista."
        )

    if paginas[
        "artista_id"
    ].duplicated().any():
        raise ValueError(
            "Existem artista_id duplicados."
        )


def mostrar_resultado(
    paginas,
):
    encontrados = paginas[
        "status_pagina_kworb"
    ].eq(
        "encontrado"
    ).sum()

    nao_encontrados = paginas[
        "status_pagina_kworb"
    ].eq(
        "não encontrado"
    ).sum()

    ambiguos = paginas[
        "status_pagina_kworb"
    ].eq(
        "ambíguo"
    ).sum()

    baixados = paginas[
        "status_download"
    ].eq(
        "baixado"
    ).sum()

    erros = paginas[
        "status_download"
    ].eq(
        "erro"
    ).sum()

    print(
        "\nCATÁLOGO DE PÁGINAS CONCLUÍDO"
    )

    print(
        f"Artistas analisados: "
        f"{len(paginas)}"
    )

    print(
        f"Páginas encontradas: "
        f"{encontrados}"
    )

    print(
        f"Páginas não encontradas: "
        f"{nao_encontrados}"
    )

    print(
        f"Casos ambíguos: "
        f"{ambiguos}"
    )

    print(
        f"Páginas baixadas: "
        f"{baixados}"
    )

    print(
        f"Erros de download: "
        f"{erros}"
    )

    print(
        "\nResultado por artista:"
    )

    print(
        paginas[
            [
                "nome_artista",
                "status_pagina_kworb",
                "nome_kworb",
                "slug_kworb",
                "status_download",
            ]
        ].to_string(
            index=False
        )
    )

    print(
        f"\nMapeamento salvo em: "
        f"{ARQUIVO_PAGINAS}"
    )


def main():
    print(
        "COLETANDO PÁGINAS INDIVIDUAIS "
        "DOS ARTISTAS NO KWORB"
    )

    if not ARQUIVO_MAPEAMENTO.exists():
        print(
            f"\nERRO: mapeamento não encontrado: "
            f"{ARQUIVO_MAPEAMENTO}"
        )

        return

    try:
        mapeamento = pd.read_csv(
            ARQUIVO_MAPEAMENTO,
            encoding="utf-8-sig",
            dtype=str,
        ).fillna("")

        sessao = requests.Session()

        catalogo = construir_catalogo(
            sessao
        )

        paginas = mapear_paginas(
            mapeamento=mapeamento,
            catalogo=catalogo,
        )

        paginas = baixar_paginas_artistas(
            sessao=sessao,
            paginas=paginas,
        )

        validar_resultado(
            mapeamento=mapeamento,
            paginas=paginas,
        )

    except (
        requests.RequestException,
        ValueError,
    ) as erro:
        print(
            f"\nERRO: {erro}"
        )

        return

    paginas.to_csv(
        ARQUIVO_PAGINAS,
        index=False,
        encoding="utf-8-sig",
    )

    mostrar_resultado(
        paginas
    )


if __name__ == "__main__":
    main()