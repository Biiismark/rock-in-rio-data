from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import re
import unicodedata

import pandas as pd
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode


URL_FONTE = (
    "https://kworb.net/spotify/country/"
    "br_daily_totals.html"
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

PASTA_BRUTOS = (
    PASTA_PROJETO
    / "dados"
    / "brutos"
    / "spotify_historico_brasil"
)

PASTA_TRATADOS = (
    PASTA_PROJETO
    / "dados"
    / "tratados"
)

ARQUIVO_SAIDA = (
    PASTA_TRATADOS
    / "spotify_historico_brasil.csv"
)

PASTA_BRUTOS.mkdir(
    parents=True,
    exist_ok=True,
)

PASTA_TRATADOS.mkdir(
    parents=True,
    exist_ok=True,
)


def limpar_texto(texto):
    if texto is None or pd.isna(texto):
        return ""

    texto = unicodedata.normalize(
        "NFKC",
        str(texto),
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


def normalizar_texto(texto):
    texto = limpar_texto(texto)
    texto = unidecode(texto).lower()

    texto = re.sub(
        r"[^a-z0-9]+",
        "_",
        texto,
    )

    return texto.strip("_")


def converter_inteiro(valor):
    valor = limpar_texto(valor)

    if valor.lower() in {
        "",
        "-",
        "—",
        "nan",
        "none",
    }:
        return None

    valor = re.sub(
        r"[^\d-]",
        "",
        valor,
    )

    if valor in {
        "",
        "-",
    }:
        return None

    try:
        return int(valor)

    except ValueError:
        return None


def separar_artista_titulo(texto):
    texto = limpar_texto(texto)

    resultado = re.match(
        r"^(.*?)\s+-\s*(.*)$",
        texto,
    )

    if not resultado:
        return texto, ""

    artista = limpar_texto(
        resultado.group(1)
    )

    titulo = limpar_texto(
        resultado.group(2)
    )

    return (
        artista,
        titulo,
    )


def baixar_pagina():
    resposta = requests.get(
        URL_FONTE,
        headers=CABECALHOS,
        timeout=60,
    )

    resposta.raise_for_status()
    resposta.encoding = "utf-8"

    return resposta.text


def extrair_periodo_cobertura(sopa):
    texto_pagina = limpar_texto(
        sopa.get_text(
            " ",
            strip=True,
        )
    )

    resultado = re.search(
        r"Covers charts from "
        r"(\d{4}/\d{2}/\d{2}) "
        r"to "
        r"(\d{4}/\d{2}/\d{2})",
        texto_pagina,
        flags=re.IGNORECASE,
    )

    if not resultado:
        raise ValueError(
            "Não foi possível identificar o "
            "período coberto pela fonte."
        )

    data_inicio = (
        resultado
        .group(1)
        .replace("/", "-")
    )

    data_fim = (
        resultado
        .group(2)
        .replace("/", "-")
    )

    return (
        data_inicio,
        data_fim,
    )


def extrair_tabela(html):
    sopa = BeautifulSoup(
        html,
        "lxml",
    )

    tabela_html = sopa.find("table")

    if tabela_html is None:
        raise ValueError(
            "Nenhuma tabela encontrada."
        )

    registros = []

    for linha in tabela_html.find_all("tr"):
        celulas = linha.find_all("td")

        if len(celulas) < 7:
            continue

        link_faixa = celulas[0].find(
            "a",
            href=re.compile(
                r"track/([A-Za-z0-9]+)\.html"
            ),
        )

        if link_faixa is None:
            continue

        resultado_id = re.search(
            r"track/([A-Za-z0-9]+)\.html",
            link_faixa.get(
                "href",
                "",
            ),
        )

        if not resultado_id:
            continue

        spotify_track_id = (
            resultado_id.group(1)
        )

        item_bruto = limpar_texto(
            celulas[0].get_text(
                " ",
                strip=True,
            )
        )

        registros.append(
            {
                "Artist and Title": item_bruto,
                "spotify_track_id": (
                    spotify_track_id
                ),
                "Days": limpar_texto(
                    celulas[1].get_text(
                        " ",
                        strip=True,
                    )
                ),
                "T10": limpar_texto(
                    celulas[2].get_text(
                        " ",
                        strip=True,
                    )
                ),
                "Pk": limpar_texto(
                    celulas[3].get_text(
                        " ",
                        strip=True,
                    )
                ),
                "(x?)": limpar_texto(
                    celulas[4].get_text(
                        " ",
                        strip=True,
                    )
                ),
                "PkStreams": limpar_texto(
                    celulas[5].get_text(
                        " ",
                        strip=True,
                    )
                ),
                "Total": limpar_texto(
                    celulas[6].get_text(
                        " ",
                        strip=True,
                    )
                ),
            }
        )

    tabela = pd.DataFrame(
        registros
    )

    if tabela.empty:
        raise ValueError(
            "A tabela foi encontrada, mas os "
            "IDs das músicas não foram extraídos."
        )

    return tabela


def transformar_dados(
    tabela,
    coletado_em,
    data_inicio,
    data_fim,
):
    registros = []

    for _, linha in tabela.iterrows():
        item_bruto = limpar_texto(
            linha.get(
                "Artist and Title"
            )
        )

        spotify_track_id = limpar_texto(
            linha.get(
                "spotify_track_id"
            )
        )

        if not item_bruto:
            continue

        if not spotify_track_id:
            continue

        (
            artista,
            titulo,
        ) = separar_artista_titulo(
            item_bruto
        )

        if not artista:
            continue

        titulo_disponivel = bool(
            titulo
        )

        registros.append(
            {
                "data_referencia": data_fim,
                "coletado_em": coletado_em,
                "inicio_cobertura": data_inicio,
                "fim_cobertura": data_fim,
                "fonte": (
                    "spotify_daily_totals_brasil"
                ),
                "plataforma": "Spotify",
                "pais": "Brasil",
                "tipo_item": "Música",
                "periodicidade": (
                    "Histórico acumulado"
                ),
                "musica_id": spotify_track_id,
                "spotify_track_id": (
                    spotify_track_id
                ),
                "artista": artista,
                "artista_normalizado": (
                    normalizar_texto(
                        artista
                    )
                ),
                "titulo": titulo,
                "titulo_normalizado": (
                    normalizar_texto(
                        titulo
                    )
                ),
                "titulo_disponivel": (
                    titulo_disponivel
                ),
                "registro_incompleto_fonte": (
                    not titulo_disponivel
                ),
                "item_bruto": item_bruto,
                "dias_no_ranking": (
                    converter_inteiro(
                        linha.get("Days")
                    )
                ),
                "dias_top_10": (
                    converter_inteiro(
                        linha.get("T10")
                    )
                ),
                "pico": converter_inteiro(
                    linha.get("Pk")
                ),
                "vezes_no_pico": (
                    converter_vezes_pico(
                        linha.get("(x?)")
                    )
                ),
                "streams_no_pico": (
                    converter_inteiro(
                        linha.get(
                            "PkStreams"
                        )
                    )
                ),
                "streams_acumulados_ranking": (
                    converter_inteiro(
                        linha.get("Total")
                    )
                ),
                "url_fonte": URL_FONTE,
            }
        )

    dados = pd.DataFrame(
        registros
    )

    if dados.empty:
        raise ValueError(
            "A tabela foi encontrada, mas "
            "nenhum registro válido foi produzido."
        )

    return dados


def converter_vezes_pico(valor):
    valor = limpar_texto(valor)

    resultado = re.search(
        r"x(\d+)",
        valor,
    )

    if not resultado:
        return None

    return int(
        resultado.group(1)
    )


def tratar_duplicidades(dados):
    chaves = [
        "spotify_track_id",
    ]

    mascara_duplicados = (
        dados.duplicated(
            subset=chaves,
            keep=False,
        )
    )

    duplicados = dados[
        mascara_duplicados
    ].copy()

    quantidade_removida = (
        len(dados)
        - len(
            dados.drop_duplicates(
                subset=chaves
            )
        )
    )

    if not duplicados.empty:
        print(
            "\nALERTA DE QUALIDADE"
        )

        print(
            "O mesmo ID do Spotify apareceu "
            "mais de uma vez. O maior total "
            "será preservado."
        )

        for _, linha in (
            duplicados
            .sort_values(
                [
                    "spotify_track_id",
                    "streams_acumulados_ranking",
                ],
                ascending=[
                    True,
                    False,
                ],
            )
            .iterrows()
        ):
            print(
                f" - ID "
                f"{linha['spotify_track_id']} | "
                f"{linha['item_bruto']} | "
                f"{linha['streams_acumulados_ranking']}"
            )

    dados_unicos = (
        dados
        .sort_values(
            "streams_acumulados_ranking",
            ascending=False,
            na_position="last",
        )
        .drop_duplicates(
            subset=chaves,
            keep="first",
        )
        .reset_index(
            drop=True
        )
    )

    return (
        dados_unicos,
        quantidade_removida,
    )


def validar_dados(
    dados,
    quantidade_bruta,
):
    problemas = []

    if quantidade_bruta < 5000:
        problemas.append(
            "A fonte retornou menos de "
            "5.000 músicas."
        )

    if len(dados) < 5000:
        problemas.append(
            "Menos de 5.000 registros "
            "foram tratados."
        )

    if dados[
        "spotify_track_id"
    ].eq("").any():
        problemas.append(
            "Existem IDs do Spotify vazios."
        )

    if dados[
        "spotify_track_id"
    ].duplicated().any():
        problemas.append(
            "Ainda existem IDs do Spotify "
            "duplicados após o tratamento."
        )

    if dados[
        "artista"
    ].eq("").any():
        problemas.append(
            "Existem artistas vazios."
        )

    quantidade_titulos_vazios = (
        dados[
            "titulo"
        ].eq("").sum()
    )

    if quantidade_titulos_vazios > 10:
        problemas.append(
            "A fonte retornou mais de 10 "
            "registros sem título."
        )

    if (
        dados[
            "streams_acumulados_ranking"
        ]
        .isna()
        .all()
    ):
        problemas.append(
            "Todos os totais de streams "
            "estão vazios."
        )

    if (
        dados[
            "dias_no_ranking"
        ]
        .dropna()
        .lt(1)
        .any()
    ):
        problemas.append(
            "Existem valores inválidos em "
            "dias no ranking."
        )

    if problemas:
        raise ValueError(
            "Falha na validação:\n - "
            + "\n - ".join(
                problemas
            )
        )


def salvar_html(
    html,
    data_fim,
):
    arquivo_html = (
        PASTA_BRUTOS
        / (
            "spotify_daily_totals_br_"
            f"{data_fim}.html"
        )
    )

    arquivo_html.write_text(
        html,
        encoding="utf-8",
    )

    return arquivo_html


def main():
    agora = datetime.now(
        FUSO_BRASIL
    )

    coletado_em = agora.isoformat(
        timespec="seconds"
    )

    print(
        "COLETANDO HISTÓRICO DO "
        "SPOTIFY BRASIL"
    )

    try:
        html = baixar_pagina()

        sopa = BeautifulSoup(
            html,
            "lxml",
        )

        (
            data_inicio,
            data_fim,
        ) = extrair_periodo_cobertura(
            sopa
        )

        print(
            f"Período da fonte: "
            f"{data_inicio} até {data_fim}"
        )

        tabela = extrair_tabela(
            html
        )

        quantidade_bruta = len(
            tabela
        )

        print(
            f"Registros brutos: "
            f"{quantidade_bruta}"
        )

        dados = transformar_dados(
            tabela=tabela,
            coletado_em=coletado_em,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        (
            dados_unicos,
            duplicidades_removidas,
        ) = tratar_duplicidades(
            dados
        )

        validar_dados(
            dados=dados_unicos,
            quantidade_bruta=quantidade_bruta,
        )

    except requests.RequestException as erro:
        print(
            f"\nERRO DE ACESSO: {erro}"
        )
        return

    except ValueError as erro:
        print(
            f"\nERRO DE VALIDAÇÃO: {erro}"
        )
        return

    arquivo_html = salvar_html(
        html=html,
        data_fim=data_fim,
    )

    dados_unicos.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        encoding="utf-8-sig",
    )

    quantidade_incompletos = int(
        dados_unicos[
            "registro_incompleto_fonte"
        ].sum()
    )

    print(
        "\nCOLETA CONCLUÍDA"
    )

    print(
        f"Registros tratados: "
        f"{len(dados_unicos)}"
    )

    print(
        f"Duplicidades reais de ID removidas: "
        f"{duplicidades_removidas}"
    )

    print(
        f"Registros incompletos da fonte: "
        f"{quantidade_incompletos}"
    )

    print(
        "Maior total acumulado: "
        f"{dados_unicos['streams_acumulados_ranking'].max():,.0f}"
    )

    print(
        "Artistas distintos: "
        f"{dados_unicos['artista_normalizado'].nunique()}"
    )

    print(
        "IDs distintos do Spotify: "
        f"{dados_unicos['spotify_track_id'].nunique()}"
    )

    print(
        f"\nArquivo salvo em: "
        f"{ARQUIVO_SAIDA}"
    )

    print(
        f"HTML preservado em: "
        f"{arquivo_html}"
    )

    print(
        "\nOBSERVAÇÃO: os streams representam "
        "somente os períodos em que cada música "
        "permaneceu no Top 200 brasileiro."
    )


if __name__ == "__main__":
    main()