from io import StringIO
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup


FONTES = {
    "kworb_home": (
        "https://kworb.net/"
    ),
    "current_charts": (
        "https://kworb.net/charts/"
    ),
    "current_charts_artistas": (
        "https://kworb.net/charts/index_a.html"
    ),
    "itunes_brasil": (
        "https://kworb.net/charts/itunes/br.html"
    ),
    "apple_musicas_brasil": (
        "https://kworb.net/charts/apple_s/br.html"
    ),
    "apple_albuns_brasil": (
        "https://kworb.net/charts/apple_a/br.html"
    ),
    "apple_itunes_brasil": (
        "https://kworb.net/charts/aitunes/br.html"
    ),
    "shazam_brasil": (
        "https://kworb.net/charts/shazam/br.html"
    ),
    "deezer_brasil": (
        "https://kworb.net/charts/deezer/br.html"
    ),
    "spotify_inicio": (
        "https://kworb.net/spotify/"
    ),
    "spotify_diario_brasil": (
        "https://kworb.net/spotify/country/br_daily.html"
    ),
    "spotify_diario_totais_brasil": (
        "https://kworb.net/spotify/country/"
        "br_daily_totals.html"
    ),
    "spotify_semanal_brasil": (
        "https://kworb.net/spotify/country/"
        "br_weekly.html"
    ),
    "spotify_semanal_totais_brasil": (
        "https://kworb.net/spotify/country/"
        "br_weekly_totals.html"
    ),
    "spotify_artistas": (
        "https://kworb.net/spotify/artists.html"
    ),
    "spotify_ouvintes": (
        "https://kworb.net/spotify/listeners.html"
    ),
    "spotify_top_lists": (
        "https://kworb.net/spotify/toplists.html"
    ),
    "youtube_inicio": (
        "https://kworb.net/youtube/"
    ),
    "youtube_diario_brasil": (
        "https://kworb.net/youtube/insights/br_daily.html"
    ),
    "youtube_semanal_brasil": (
        "https://kworb.net/youtube/insights/br.html"
    ),
    "youtube_trending_mundial": (
        "https://kworb.net/youtube/trending.html"
    ),
    "youtube_top_lists": (
        "https://kworb.net/youtube/stats.html"
    ),
    "ranking_digital_global": (
        "https://kworb.net/itunes/"
    ),
}

CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
}

PALAVRAS_RELEVANTES = {
    "spotify",
    "youtube",
    "itunes",
    "apple",
    "deezer",
    "shazam",
    "chart",
    "charts",
    "insights",
    "listeners",
    "artists",
    "toplists",
    "country",
    "brazil",
    "brasil",
}

CAMINHOS_IGNORADOS = {
    "/artist/",
    "/track/",
    "/video/",
}

PASTA_PROJETO = Path(__file__).resolve().parents[1]

PASTA_AUDITORIA = (
    PASTA_PROJETO
    / "dados"
    / "brutos"
    / "auditoria_kworb"
)

PASTA_REFERENCIAS = (
    PASTA_PROJETO
    / "dados"
    / "referencias"
)

PASTA_AUDITORIA.mkdir(
    parents=True,
    exist_ok=True,
)

PASTA_REFERENCIAS.mkdir(
    parents=True,
    exist_ok=True,
)

ARQUIVO_CATALOGO = (
    PASTA_REFERENCIAS
    / "catalogo_fontes_kworb.csv"
)

ARQUIVO_LINKS = (
    PASTA_REFERENCIAS
    / "links_relevantes_kworb.csv"
)


def limpar_texto(texto):
    return " ".join(
        str(texto).split()
    )


def link_relevante(url, texto):
    analisado = f"{url} {texto}".lower()
    caminho = urlparse(url).path.lower()

    if any(
        ignorado in caminho
        for ignorado in CAMINHOS_IGNORADOS
    ):
        return False

    return any(
        palavra in analisado
        for palavra in PALAVRAS_RELEVANTES
    )


def analisar_tabelas(html):
    try:
        tabelas = pd.read_html(
            StringIO(html)
        )

    except ValueError:
        return 0, "", ""

    formatos = []
    colunas_encontradas = []

    for numero, tabela in enumerate(
        tabelas,
        start=1,
    ):
        formatos.append(
            f"T{numero}:{len(tabela)}x"
            f"{len(tabela.columns)}"
        )

        colunas = [
            limpar_texto(coluna)
            for coluna in tabela.columns
        ]

        colunas_encontradas.append(
            f"T{numero}: "
            + " | ".join(colunas)
        )

    return (
        len(tabelas),
        "; ".join(formatos),
        " || ".join(colunas_encontradas),
    )


def analisar_fonte(nome, url):
    try:
        resposta = requests.get(
            url,
            headers=CABECALHOS,
            timeout=30,
        )

        resposta.raise_for_status()
        resposta.encoding = "utf-8"

    except requests.RequestException as erro:
        print(f"\nERRO: {nome}")
        print(f"Detalhe: {erro}")

        return (
            {
                "fonte": nome,
                "url": url,
                "status_http": "",
                "titulo": "",
                "titulo_pagina": "",
                "caracteres": 0,
                "quantidade_tabelas": 0,
                "formatos_tabelas": "",
                "colunas_tabelas": "",
                "menciona_brasil": False,
                "erro": str(erro),
            },
            [],
        )

    html = resposta.text
    sopa = BeautifulSoup(html, "lxml")

    arquivo_html = (
        PASTA_AUDITORIA / f"{nome}.html"
    )

    arquivo_html.write_text(
        html,
        encoding="utf-8",
    )

    titulo = (
        limpar_texto(
            sopa.title.get_text(
                " ",
                strip=True,
            )
        )
        if sopa.title
        else ""
    )

    titulo_pagina_elemento = (
        sopa.select_one(".pagetitle")
        or sopa.find("h1")
        or sopa.find("h2")
    )

    titulo_pagina = (
        limpar_texto(
            titulo_pagina_elemento.get_text(
                " ",
                strip=True,
            )
        )
        if titulo_pagina_elemento
        else ""
    )

    (
        quantidade_tabelas,
        formatos_tabelas,
        colunas_tabelas,
    ) = analisar_tabelas(html)

    texto_pagina = sopa.get_text(
        " ",
        strip=True,
    ).lower()

    links_descobertos = []

    for link in sopa.find_all(
        "a",
        href=True,
    ):
        texto_link = limpar_texto(
            link.get_text(
                " ",
                strip=True,
            )
        )

        url_completa = urljoin(
            url,
            link["href"],
        )

        url_completa = urldefrag(
            url_completa
        ).url

        dominio = urlparse(
            url_completa
        ).netloc.lower()

        if dominio not in {
            "kworb.net",
            "www.kworb.net",
        }:
            continue

        if not link_relevante(
            url=url_completa,
            texto=texto_link,
        ):
            continue

        links_descobertos.append(
            {
                "pagina_origem": nome,
                "texto_link": texto_link,
                "url": url_completa,
            }
        )

    registro = {
        "fonte": nome,
        "url": url,
        "status_http": resposta.status_code,
        "titulo": titulo,
        "titulo_pagina": titulo_pagina,
        "caracteres": len(html),
        "quantidade_tabelas": quantidade_tabelas,
        "formatos_tabelas": formatos_tabelas,
        "colunas_tabelas": colunas_tabelas,
        "menciona_brasil": (
            "brazil" in texto_pagina
            or "brasil" in texto_pagina
        ),
        "erro": "",
    }

    print(f"\nFONTE: {nome}")
    print(f"Status: {resposta.status_code}")
    print(f"Título: {titulo}")
    print(
        f"Tabelas: {quantidade_tabelas} "
        f"({formatos_tabelas})"
    )
    print(
        "Links relevantes encontrados: "
        f"{len(links_descobertos)}"
    )

    return registro, links_descobertos


def main():
    print("INICIANDO AUDITORIA DO KWORB")

    catalogo = []
    todos_links = []

    for nome, url in FONTES.items():
        registro, links = analisar_fonte(
            nome=nome,
            url=url,
        )

        catalogo.append(registro)
        todos_links.extend(links)

        time.sleep(1)

    catalogo_df = pd.DataFrame(catalogo)

    links_df = pd.DataFrame(todos_links)

    if not links_df.empty:
        links_df = (
            links_df
            .drop_duplicates(
                subset=["url"]
            )
            .sort_values(
                [
                    "pagina_origem",
                    "texto_link",
                ]
            )
            .reset_index(drop=True)
        )

    catalogo_df.to_csv(
        ARQUIVO_CATALOGO,
        index=False,
        encoding="utf-8-sig",
    )

    links_df.to_csv(
        ARQUIVO_LINKS,
        index=False,
        encoding="utf-8-sig",
    )

    print("\nAUDITORIA CONCLUÍDA")
    print(
        f"Fontes verificadas: "
        f"{len(catalogo_df)}"
    )
    print(
        f"Links relevantes únicos: "
        f"{len(links_df)}"
    )
    print(f"\nCatálogo: {ARQUIVO_CATALOGO}")
    print(f"Links: {ARQUIVO_LINKS}")
    print(f"HTMLs: {PASTA_AUDITORIA}")


if __name__ == "__main__":
    main()