from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import re
import unicodedata

import pandas as pd
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode


URL = "https://kworb.net/spotify/country/br_daily.html"

CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
}

PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_BRUTOS = PASTA_PROJETO / "dados" / "brutos"
PASTA_TRATADOS = PASTA_PROJETO / "dados" / "tratados"

PASTA_BRUTOS.mkdir(parents=True, exist_ok=True)
PASTA_TRATADOS.mkdir(parents=True, exist_ok=True)

ARQUIVO_RANKING = (
    PASTA_TRATADOS / "spotify_ranking_diario.csv"
)

ARQUIVO_CREDITOS = (
    PASTA_TRATADOS / "spotify_creditos_diario.csv"
)


def limpar_texto(texto):
    if texto is None:
        return ""

    texto = unicodedata.normalize("NFKC", str(texto))
    texto = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def normalizar_nome(nome):
    nome = limpar_texto(nome)
    nome = unidecode(nome).lower()
    nome = re.sub(r"[^a-z0-9]+", "_", nome)

    return nome.strip("_")


def converter_inteiro(valor):
    valor = limpar_texto(valor)
    valor = valor.replace(",", "")
    valor = valor.replace(".", "")

    if valor in {"", "-", "—"}:
        return None

    try:
        return int(valor)

    except ValueError:
        return None


def converter_variacao_posicao(valor):
    valor = limpar_texto(valor)

    if valor == "=":
        return 0

    if valor.lower() in {"new", "novo"}:
        return None

    try:
        return int(valor)

    except ValueError:
        return None


def extrair_id_link(link, tipo):
    if not link:
        return ""

    href = link.get("href", "")

    padrao = rf"/{tipo}/([A-Za-z0-9]+)\.html"
    resultado = re.search(padrao, href)

    if resultado:
        return resultado.group(1)

    return ""


def extrair_data_ranking(sopa):
    titulo = sopa.select_one(".pagetitle")

    if not titulo:
        raise ValueError(
            "Título da página do Kworb não encontrado."
        )

    texto_titulo = limpar_texto(
        titulo.get_text(" ", strip=True)
    )

    resultado = re.search(
        r"(\d{4})/(\d{2})/(\d{2})",
        texto_titulo,
    )

    if not resultado:
        raise ValueError(
            "Data do ranking não encontrada no Kworb."
        )

    ano, mes, dia = resultado.groups()

    return f"{ano}-{mes}-{dia}"


def baixar_pagina():
    resposta = requests.get(
        URL,
        headers=CABECALHOS,
        timeout=30,
    )

    resposta.raise_for_status()
    resposta.encoding = "utf-8"

    return resposta.text


def extrair_ranking(html):
    sopa = BeautifulSoup(html, "lxml")
    data_ranking = extrair_data_ranking(sopa)

    tabela = sopa.select_one("table#spotifydaily")

    if not tabela:
        raise ValueError(
            "Tabela spotifydaily não encontrada."
        )

    coletado_em = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    ).isoformat(timespec="seconds")

    registros_ranking = []
    registros_creditos = []

    linhas = tabela.select("tr")

    for linha in linhas:
        colunas = linha.find_all("td")

        if len(colunas) < 11:
            continue

        posicao = converter_inteiro(
            colunas[0].get_text(" ", strip=True)
        )

        if posicao is None:
            continue

        movimento = limpar_texto(
            colunas[1].get_text(" ", strip=True)
        )

        celula_musica = colunas[2]
        links = celula_musica.find_all("a")

        link_faixa = next(
            (
                link
                for link in links
                if "../track/" in link.get("href", "")
            ),
            None,
        )

        if not link_faixa:
            continue

        faixa_id = extrair_id_link(
            link_faixa,
            "track",
        )

        nome_faixa = limpar_texto(
            link_faixa.get_text(" ", strip=True)
        )

        indice_faixa = links.index(link_faixa)

        links_artistas_principais = [
            link
            for link in links[:indice_faixa]
            if "../artist/" in link.get("href", "")
        ]

        links_participacoes = [
            link
            for link in links[indice_faixa + 1:]
            if "../artist/" in link.get("href", "")
        ]

        if links_artistas_principais:
            link_principal = links_artistas_principais[0]

            artista_principal_id = extrair_id_link(
                link_principal,
                "artist",
            )

            artista_principal = limpar_texto(
                link_principal.get_text(" ", strip=True)
            )

        else:
            artista_principal_id = ""
            artista_principal = ""

        vezes_pico_texto = limpar_texto(
            colunas[5].get_text(" ", strip=True)
        )

        resultado_vezes_pico = re.search(
            r"x(\d+)",
            vezes_pico_texto,
        )

        vezes_pico = (
            int(resultado_vezes_pico.group(1))
            if resultado_vezes_pico
            else None
        )

        registros_ranking.append(
            {
                "data_ranking": data_ranking,
                "plataforma": "Spotify",
                "pais": "Brasil",
                "posicao": posicao,
                "movimento_posicao": movimento,
                "variacao_posicao": (
                    converter_variacao_posicao(movimento)
                ),
                "faixa_id": faixa_id,
                "faixa": nome_faixa,
                "artista_principal_id": artista_principal_id,
                "artista_principal": artista_principal,
                "artista_principal_normalizado": (
                    normalizar_nome(artista_principal)
                ),
                "dias_no_ranking": converter_inteiro(
                    colunas[3].get_text(" ", strip=True)
                ),
                "pico": converter_inteiro(
                    colunas[4].get_text(" ", strip=True)
                ),
                "vezes_no_pico": vezes_pico,
                "streams_dia": converter_inteiro(
                    colunas[6].get_text(" ", strip=True)
                ),
                "variacao_streams_dia": converter_inteiro(
                    colunas[7].get_text(" ", strip=True)
                ),
                "streams_7_dias": converter_inteiro(
                    colunas[8].get_text(" ", strip=True)
                ),
                "variacao_streams_7_dias": converter_inteiro(
                    colunas[9].get_text(" ", strip=True)
                ),
                "streams_total": converter_inteiro(
                    colunas[10].get_text(" ", strip=True)
                ),
                "url_fonte": URL,
                "coletado_em": coletado_em,
            }
        )

        ordem_credito = 1

        for link in links_artistas_principais:
            registros_creditos.append(
                {
                    "data_ranking": data_ranking,
                    "faixa_id": faixa_id,
                    "artista_spotify_id": extrair_id_link(
                        link,
                        "artist",
                    ),
                    "artista": limpar_texto(
                        link.get_text(" ", strip=True)
                    ),
                    "artista_normalizado": normalizar_nome(
                        link.get_text(" ", strip=True)
                    ),
                    "ordem_credito": ordem_credito,
                    "tipo_credito": "principal",
                }
            )

            ordem_credito += 1

        for link in links_participacoes:
            registros_creditos.append(
                {
                    "data_ranking": data_ranking,
                    "faixa_id": faixa_id,
                    "artista_spotify_id": extrair_id_link(
                        link,
                        "artist",
                    ),
                    "artista": limpar_texto(
                        link.get_text(" ", strip=True)
                    ),
                    "artista_normalizado": normalizar_nome(
                        link.get_text(" ", strip=True)
                    ),
                    "ordem_credito": ordem_credito,
                    "tipo_credito": "participacao",
                }
            )

            ordem_credito += 1

    ranking = pd.DataFrame(registros_ranking)
    creditos = pd.DataFrame(registros_creditos)

    return data_ranking, ranking, creditos


def atualizar_historico(
    novos_dados,
    caminho,
    chaves,
    ordenacao,
):
    if caminho.exists():
        historico = pd.read_csv(
            caminho,
            encoding="utf-8-sig",
        )

        resultado = pd.concat(
            [historico, novos_dados],
            ignore_index=True,
        )

    else:
        resultado = novos_dados.copy()

    resultado = (
        resultado
        .drop_duplicates(
            subset=chaves,
            keep="last",
        )
        .sort_values(ordenacao)
        .reset_index(drop=True)
    )

    resultado.to_csv(
        caminho,
        index=False,
        encoding="utf-8-sig",
    )

    return resultado


def main():
    print("Acessando o ranking do Spotify Brasil...")

    try:
        html = baixar_pagina()
        data_ranking, ranking, creditos = extrair_ranking(
            html
        )

    except requests.RequestException as erro:
        print("Não foi possível acessar o Kworb.")
        print(f"Detalhe: {erro}")
        return

    except ValueError as erro:
        print("Não foi possível interpretar o Kworb.")
        print(f"Detalhe: {erro}")
        return

    arquivo_html = (
        PASTA_BRUTOS
        / f"kworb_spotify_br_{data_ranking}.html"
    )

    arquivo_html.write_text(
        html,
        encoding="utf-8",
    )

    historico_ranking = atualizar_historico(
        novos_dados=ranking,
        caminho=ARQUIVO_RANKING,
        chaves=["data_ranking", "faixa_id"],
        ordenacao=["data_ranking", "posicao"],
    )

    historico_creditos = atualizar_historico(
        novos_dados=creditos,
        caminho=ARQUIVO_CREDITOS,
        chaves=[
            "data_ranking",
            "faixa_id",
            "artista_spotify_id",
        ],
        ordenacao=[
            "data_ranking",
            "faixa_id",
            "ordem_credito",
        ],
    )

    print("\nCOLETA CONCLUÍDA")
    print(f"Data do ranking: {data_ranking}")
    print(f"Faixas coletadas hoje: {len(ranking)}")
    print(f"Créditos de artistas coletados: {len(creditos)}")
    print(
        "Faixas acumuladas no histórico: "
        f"{len(historico_ranking)}"
    )
    print(
        "Créditos acumulados no histórico: "
        f"{len(historico_creditos)}"
    )
    print(f"\nRanking salvo em: {ARQUIVO_RANKING}")
    print(f"Créditos salvos em: {ARQUIVO_CREDITOS}")
    print(f"HTML bruto salvo em: {arquivo_html}")


if __name__ == "__main__":
    main()