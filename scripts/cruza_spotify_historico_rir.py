from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup


URL_ARTISTA = (
    "https://kworb.net/spotify/artist/"
    "{spotify_artista_id}_songs.html"
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

PASTA_TRATADOS = (
    PASTA_PROJETO
    / "dados"
    / "tratados"
)

PASTA_BRUTOS = (
    PASTA_PROJETO
    / "dados"
    / "brutos"
    / "spotify_catalogos_artistas"
)

ARQUIVO_MAPEAMENTO = (
    PASTA_REFERENCIAS
    / "mapeamento_artistas_spotify.csv"
)

ARQUIVO_HISTORICO = (
    PASTA_TRATADOS
    / "spotify_historico_brasil.csv"
)

ARQUIVO_CATALOGO = (
    PASTA_TRATADOS
    / "spotify_catalogo_artistas_rir.csv"
)

ARQUIVO_FAIXAS = (
    PASTA_TRATADOS
    / "spotify_historico_rir_faixas.csv"
)

ARQUIVO_RESUMO = (
    PASTA_TRATADOS
    / "spotify_historico_rir_artistas.csv"
)

ARQUIVO_AUDITORIA = (
    PASTA_REFERENCIAS
    / "auditoria_catalogos_spotify_rir.csv"
)

PASTA_BRUTOS.mkdir(
    parents=True,
    exist_ok=True,
)


def limpar_texto(valor):
    if valor is None or pd.isna(valor):
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(valor),
    ).strip()


def carregar_arquivos():
    if not ARQUIVO_MAPEAMENTO.exists():
        raise FileNotFoundError(
            f"Mapeamento não encontrado: "
            f"{ARQUIVO_MAPEAMENTO}"
        )

    if not ARQUIVO_HISTORICO.exists():
        raise FileNotFoundError(
            f"Histórico não encontrado: "
            f"{ARQUIVO_HISTORICO}"
        )

    mapeamento = pd.read_csv(
        ARQUIVO_MAPEAMENTO,
        encoding="utf-8-sig",
        dtype=str,
    )

    historico = pd.read_csv(
        ARQUIVO_HISTORICO,
        encoding="utf-8-sig",
        dtype={
            "spotify_track_id": str,
        },
    )

    return (
        mapeamento,
        historico,
    )


def validar_arquivos(
    mapeamento,
    historico,
):
    colunas_mapeamento = {
        "artista_id",
        "nome_artista",
        "spotify_artista_id",
        "spotify_nome_artista",
    }

    colunas_historico = {
        "spotify_track_id",
        "titulo",
        "dias_no_ranking",
        "dias_top_10",
        "pico",
        "streams_no_pico",
        "streams_acumulados_ranking",
    }

    ausentes_mapeamento = (
        colunas_mapeamento
        - set(mapeamento.columns)
    )

    ausentes_historico = (
        colunas_historico
        - set(historico.columns)
    )

    if ausentes_mapeamento:
        raise ValueError(
            "Colunas ausentes no mapeamento: "
            + ", ".join(
                sorted(
                    ausentes_mapeamento
                )
            )
        )

    if ausentes_historico:
        raise ValueError(
            "Colunas ausentes no histórico: "
            + ", ".join(
                sorted(
                    ausentes_historico
                )
            )
        )

    if len(mapeamento) != 28:
        raise ValueError(
            "O mapeamento não possui "
            "exatamente 28 artistas."
        )

    ids_vazios = (
        mapeamento[
            "spotify_artista_id"
        ]
        .fillna("")
        .str.strip()
        .eq("")
    )

    if ids_vazios.any():
        raise ValueError(
            "Existem artistas sem ID "
            "do Spotify."
        )

    if mapeamento[
        "spotify_artista_id"
    ].duplicated().any():
        raise ValueError(
            "Existem IDs de artista duplicados."
        )

    if historico[
        "spotify_track_id"
    ].duplicated().any():
        raise ValueError(
            "Existem IDs de faixa duplicados "
            "no histórico brasileiro."
        )


def baixar_catalogo(
    spotify_artista_id,
):
    url = URL_ARTISTA.format(
        spotify_artista_id=(
            spotify_artista_id
        )
    )

    resposta = requests.get(
        url,
        headers=CABECALHOS,
        timeout=60,
    )

    resposta.raise_for_status()
    resposta.encoding = "utf-8"

    return (
        url,
        resposta.text,
    )


def extrair_faixas_catalogo(
    html,
    artista_id,
    nome_artista,
    spotify_artista_id,
    spotify_nome_artista,
    url_fonte,
    coletado_em,
):
    sopa = BeautifulSoup(
        html,
        "lxml",
    )

    registros = []

    padrao_faixa = re.compile(
        r"(?:open\.spotify\.com/)"
        r"(?:intl-[a-z]+/)?"
        r"track/"
        r"([A-Za-z0-9]{22})"
    )

    for link in sopa.find_all(
        "a",
        href=True,
    ):
        href = limpar_texto(
            link.get("href")
        )

        resultado = padrao_faixa.search(
            href
        )

        if not resultado:
            continue

        spotify_track_id = (
            resultado.group(1)
        )

        titulo_catalogo = limpar_texto(
            link.get_text(
                " ",
                strip=True,
            )
        )

        linha_html = link.find_parent(
            "tr"
        )

        texto_linha = (
            limpar_texto(
                linha_html.get_text(
                    " ",
                    strip=True,
                )
            )
            if linha_html
            else titulo_catalogo
        )

        tipo_credito = (
            "participacao"
            if texto_linha.startswith("*")
            else "principal"
        )

        registros.append(
            {
                "artista_id": artista_id,
                "nome_artista": nome_artista,
                "spotify_artista_id": (
                    spotify_artista_id
                ),
                "spotify_nome_artista": (
                    spotify_nome_artista
                ),
                "spotify_track_id": (
                    spotify_track_id
                ),
                "titulo_catalogo": (
                    titulo_catalogo
                ),
                "tipo_credito_catalogo": (
                    tipo_credito
                ),
                "url_catalogo_artista": (
                    url_fonte
                ),
                "coletado_em": coletado_em,
            }
        )

    catalogo = pd.DataFrame(
        registros
    )

    if catalogo.empty:
        return catalogo

    catalogo = (
        catalogo
        .drop_duplicates(
            subset=[
                "artista_id",
                "spotify_track_id",
            ],
            keep="first",
        )
        .reset_index(
            drop=True
        )
    )

    return catalogo


def coletar_catalogos(
    mapeamento,
):
    agora = datetime.now(
        FUSO_BRASIL
    )

    coletado_em = agora.isoformat(
        timespec="seconds"
    )

    todos_catalogos = []
    auditoria = []

    total = len(
        mapeamento
    )

    for numero, (_, linha) in enumerate(
        mapeamento.iterrows(),
        start=1,
    ):
        artista_id = limpar_texto(
            linha["artista_id"]
        )

        nome_artista = limpar_texto(
            linha["nome_artista"]
        )

        spotify_artista_id = limpar_texto(
            linha["spotify_artista_id"]
        )

        spotify_nome_artista = limpar_texto(
            linha["spotify_nome_artista"]
        )

        print(
            f"[{numero}/{total}] "
            f"{nome_artista}"
        )

        try:
            (
                url_fonte,
                html,
            ) = baixar_catalogo(
                spotify_artista_id
            )

            catalogo = extrair_faixas_catalogo(
                html=html,
                artista_id=artista_id,
                nome_artista=nome_artista,
                spotify_artista_id=(
                    spotify_artista_id
                ),
                spotify_nome_artista=(
                    spotify_nome_artista
                ),
                url_fonte=url_fonte,
                coletado_em=coletado_em,
            )

            arquivo_html = (
                PASTA_BRUTOS
                / (
                    f"{artista_id}_"
                    f"{spotify_artista_id}.html"
                )
            )

            arquivo_html.write_text(
                html,
                encoding="utf-8",
            )

            quantidade_faixas = len(
                catalogo
            )

            print(
                f"   Faixas no catálogo: "
                f"{quantidade_faixas}"
            )

            if not catalogo.empty:
                todos_catalogos.append(
                    catalogo
                )

            auditoria.append(
                {
                    "artista_id": artista_id,
                    "nome_artista": nome_artista,
                    "spotify_artista_id": (
                        spotify_artista_id
                    ),
                    "status": "coletado",
                    "quantidade_faixas_catalogo": (
                        quantidade_faixas
                    ),
                    "url_fonte": url_fonte,
                    "erro": "",
                }
            )

        except requests.RequestException as erro:
            print(
                f"   ERRO DE ACESSO: {erro}"
            )

            auditoria.append(
                {
                    "artista_id": artista_id,
                    "nome_artista": nome_artista,
                    "spotify_artista_id": (
                        spotify_artista_id
                    ),
                    "status": "erro",
                    "quantidade_faixas_catalogo": 0,
                    "url_fonte": (
                        URL_ARTISTA.format(
                            spotify_artista_id=(
                                spotify_artista_id
                            )
                        )
                    ),
                    "erro": str(erro),
                }
            )

        time.sleep(0.3)

    if todos_catalogos:
        catalogo_completo = pd.concat(
            todos_catalogos,
            ignore_index=True,
        )

    else:
        catalogo_completo = pd.DataFrame(
            columns=[
                "artista_id",
                "nome_artista",
                "spotify_artista_id",
                "spotify_nome_artista",
                "spotify_track_id",
                "titulo_catalogo",
                "tipo_credito_catalogo",
                "url_catalogo_artista",
                "coletado_em",
            ]
        )

    auditoria = pd.DataFrame(
        auditoria
    )

    return (
        catalogo_completo,
        auditoria,
    )


def cruzar_historico(
    catalogo,
    historico,
):
    faixas = catalogo.merge(
        historico,
        on="spotify_track_id",
        how="inner",
        validate="many_to_one",
        suffixes=(
            "_catalogo",
            "_historico",
        ),
    )

    if faixas.empty:
        return faixas

    faixas = (
        faixas
        .drop_duplicates(
            subset=[
                "artista_id",
                "spotify_track_id",
            ]
        )
        .sort_values(
            [
                "nome_artista",
                "streams_acumulados_ranking",
            ],
            ascending=[
                True,
                False,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    return faixas


def criar_resumo(
    mapeamento,
    faixas,
):
    base = mapeamento[
        [
            "artista_id",
            "nome_artista",
            "spotify_artista_id",
            "spotify_nome_artista",
        ]
    ].copy()

    if faixas.empty:
        resumo_metricas = pd.DataFrame(
            columns=[
                "artista_id",
                "faixas_historico_brasil",
                "faixas_principais_historico",
                "participacoes_historico",
                "melhor_pico_historico",
                "dias_faixa_no_ranking",
                "dias_faixa_no_top_10",
                "streams_durante_ranking",
            ]
        )

    else:
        resumo_metricas = (
            faixas
            .assign(
                credito_principal=(
                    faixas[
                        "tipo_credito_catalogo"
                    ].eq("principal")
                ).astype(int),
                credito_participacao=(
                    faixas[
                        "tipo_credito_catalogo"
                    ].eq("participacao")
                ).astype(int),
            )
            .groupby(
                "artista_id",
                as_index=False,
            )
            .agg(
                faixas_historico_brasil=(
                    "spotify_track_id",
                    "nunique",
                ),
                faixas_principais_historico=(
                    "credito_principal",
                    "sum",
                ),
                participacoes_historico=(
                    "credito_participacao",
                    "sum",
                ),
                melhor_pico_historico=(
                    "pico",
                    "min",
                ),
                dias_faixa_no_ranking=(
                    "dias_no_ranking",
                    "sum",
                ),
                dias_faixa_no_top_10=(
                    "dias_top_10",
                    "sum",
                ),
                streams_durante_ranking=(
                    "streams_acumulados_ranking",
                    "sum",
                ),
            )
        )

    resumo = base.merge(
        resumo_metricas,
        on="artista_id",
        how="left",
        validate="one_to_one",
    )

    colunas_inteiras = [
        "faixas_historico_brasil",
        "faixas_principais_historico",
        "participacoes_historico",
        "dias_faixa_no_ranking",
        "dias_faixa_no_top_10",
        "streams_durante_ranking",
    ]

    for coluna in colunas_inteiras:
        resumo[coluna] = (
            resumo[coluna]
            .fillna(0)
            .astype(int)
        )

    resumo[
        "possui_historico_brasil"
    ] = (
        resumo[
            "faixas_historico_brasil"
        ] > 0
    )

    resumo = (
        resumo
        .sort_values(
            [
                "possui_historico_brasil",
                "streams_durante_ranking",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    return resumo


def validar_resultados(
    mapeamento,
    auditoria,
    catalogo,
    faixas,
    resumo,
):
    if len(auditoria) != len(mapeamento):
        raise ValueError(
            "A auditoria não possui uma "
            "linha para cada artista."
        )

    erros = auditoria[
        auditoria[
            "status"
        ].eq("erro")
    ]

    if not erros.empty:
        raise ValueError(
            "Um ou mais catálogos não foram "
            "coletados. Consulte a auditoria."
        )

    if catalogo[
        [
            "artista_id",
            "spotify_track_id",
        ]
    ].duplicated().any():
        raise ValueError(
            "Existem faixas duplicadas "
            "no catálogo por artista."
        )

    if not faixas.empty and faixas[
        [
            "artista_id",
            "spotify_track_id",
        ]
    ].duplicated().any():
        raise ValueError(
            "Existem faixas históricas "
            "duplicadas por artista."
        )

    if len(resumo) != len(mapeamento):
        raise ValueError(
            "O resumo não possui os "
            "28 artistas."
        )


def salvar_resultados(
    catalogo,
    faixas,
    resumo,
    auditoria,
):
    catalogo.to_csv(
        ARQUIVO_CATALOGO,
        index=False,
        encoding="utf-8-sig",
    )

    faixas.to_csv(
        ARQUIVO_FAIXAS,
        index=False,
        encoding="utf-8-sig",
    )

    resumo.to_csv(
        ARQUIVO_RESUMO,
        index=False,
        encoding="utf-8-sig",
    )

    auditoria.to_csv(
        ARQUIVO_AUDITORIA,
        index=False,
        encoding="utf-8-sig",
    )


def mostrar_resultado(
    catalogo,
    faixas,
    resumo,
):
    encontrados = resumo[
        resumo[
            "possui_historico_brasil"
        ]
    ]

    ausentes = resumo[
        ~resumo[
            "possui_historico_brasil"
        ]
    ]

    print(
        "\nCRUZAMENTO HISTÓRICO CONCLUÍDO"
    )

    print(
        f"Artistas analisados: "
        f"{len(resumo)}"
    )

    print(
        f"Faixas catalogadas no Spotify: "
        f"{len(catalogo)}"
    )

    print(
        "Faixas encontradas no histórico "
        f"brasileiro: {len(faixas)}"
    )

    print(
        "Artistas com histórico no "
        f"Top 200 Brasil: {len(encontrados)}"
    )

    print(
        "Artistas sem histórico no "
        f"Top 200 Brasil: {len(ausentes)}"
    )

    if not encontrados.empty:
        print(
            "\nResumo dos encontrados:"
        )

        for _, linha in (
            encontrados.iterrows()
        ):
            pico = linha[
                "melhor_pico_historico"
            ]

            pico_texto = (
                str(int(pico))
                if pd.notna(pico)
                else "sem pico"
            )

            print(
                f" - {linha['nome_artista']}: "
                f"{linha['faixas_historico_brasil']} "
                f"faixa(s), pico {pico_texto}, "
                f"{linha['streams_durante_ranking']:,} "
                f"streams durante presença "
                f"no ranking"
            )

    print(
        f"\nCatálogo salvo em: "
        f"{ARQUIVO_CATALOGO}"
    )

    print(
        f"Faixas históricas: "
        f"{ARQUIVO_FAIXAS}"
    )

    print(
        f"Resumo por artista: "
        f"{ARQUIVO_RESUMO}"
    )

    print(
        "\nIMPORTANTE: streams_durante_ranking "
        "soma somente os streams registrados "
        "enquanto cada faixa esteve no Top 200 "
        "brasileiro. Dias são dias-faixa e não "
        "dias únicos do artista."
    )


def main():
    print(
        "CRUZANDO HISTÓRICO DO SPOTIFY "
        "BRASIL COM O ROCK IN RIO 2026"
    )

    try:
        (
            mapeamento,
            historico,
        ) = carregar_arquivos()

        validar_arquivos(
            mapeamento=mapeamento,
            historico=historico,
        )

        (
            catalogo,
            auditoria,
        ) = coletar_catalogos(
            mapeamento
        )

        faixas = cruzar_historico(
            catalogo=catalogo,
            historico=historico,
        )

        resumo = criar_resumo(
            mapeamento=mapeamento,
            faixas=faixas,
        )

        validar_resultados(
            mapeamento=mapeamento,
            auditoria=auditoria,
            catalogo=catalogo,
            faixas=faixas,
            resumo=resumo,
        )

    except (
        FileNotFoundError,
        ValueError,
        pd.errors.MergeError,
    ) as erro:
        print(
            f"\nERRO: {erro}"
        )

        return

    salvar_resultados(
        catalogo=catalogo,
        faixas=faixas,
        resumo=resumo,
        auditoria=auditoria,
    )

    mostrar_resultado(
        catalogo=catalogo,
        faixas=faixas,
        resumo=resumo,
    )


if __name__ == "__main__":
    main()