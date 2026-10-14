from pathlib import Path
import re
import unicodedata

import pandas as pd
from bs4 import BeautifulSoup
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
)

ARQUIVO_MAPEAMENTO = (
    PASTA_REFERENCIAS
    / "mapeamento_artistas_spotify.csv"
)

ARQUIVO_AUDITORIA = (
    PASTA_REFERENCIAS
    / "auditoria_mapeamento_spotify.csv"
)

ARQUIVOS_FONTES = [
    (
        "spotify_artistas_global",
        PASTA_BRUTOS
        / "auditoria_kworb"
        / "spotify_artistas.html",
    ),
    (
        "spotify_ouvintes_global",
        PASTA_BRUTOS
        / "auditoria_kworb"
        / "spotify_ouvintes.html",
    ),
    (
        "spotify_historico_brasil",
        PASTA_BRUTOS
        / "spotify_historico_brasil"
        / "spotify_daily_totals_br_2026-08-24.html",
    ),
    (
        "spotify_diario_brasil",
        PASTA_BRUTOS
        / "kworb_spotify_br_2026-08-24.html",
    ),
]


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


def valor_preenchido(valor):
    if valor is None or pd.isna(valor):
        return False

    return limpar_texto(valor) != ""


def extrair_artistas_html(
    nome_fonte,
    caminho_html,
):
    if not caminho_html.exists():
        print(
            f"AVISO: fonte não encontrada: "
            f"{caminho_html}"
        )

        return []

    html = caminho_html.read_text(
        encoding="utf-8",
        errors="replace",
    )

    sopa = BeautifulSoup(
        html,
        "lxml",
    )

    registros = []

    padrao_id = re.compile(
        r"artist/"
        r"([A-Za-z0-9]{22})"
        r"(?:_songs)?"
        r"\.html"
    )

    for link in sopa.find_all(
        "a",
        href=True,
    ):
        href = limpar_texto(
            link.get("href")
        )

        resultado = padrao_id.search(
            href
        )

        if not resultado:
            continue

        spotify_artista_id = (
            resultado.group(1)
        )

        spotify_nome_artista = (
            limpar_texto(
                link.get_text(
                    " ",
                    strip=True,
                )
            )
        )

        if not spotify_nome_artista:
            continue

        registros.append(
            {
                "nome_fonte": nome_fonte,
                "spotify_artista_id": (
                    spotify_artista_id
                ),
                "spotify_nome_artista": (
                    spotify_nome_artista
                ),
                "spotify_nome_normalizado": (
                    normalizar_texto(
                        spotify_nome_artista
                    )
                ),
                "href": href,
            }
        )

    return registros


def construir_catalogo():
    todos_registros = []

    for (
        nome_fonte,
        caminho_html,
    ) in ARQUIVOS_FONTES:
        registros = extrair_artistas_html(
            nome_fonte=nome_fonte,
            caminho_html=caminho_html,
        )

        todos_registros.extend(
            registros
        )

        print(
            f"{nome_fonte}: "
            f"{len(registros)} links de artista"
        )

    if not todos_registros:
        raise ValueError(
            "Nenhum artista foi extraído "
            "dos HTMLs disponíveis."
        )

    catalogo = pd.DataFrame(
        todos_registros
    )

    catalogo = (
        catalogo
        .drop_duplicates(
            subset=[
                "spotify_artista_id",
                "spotify_nome_normalizado",
                "nome_fonte",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return catalogo


def procurar_correspondencias(
    mapeamento,
    catalogo,
):
    auditoria = []
    mapeamento_atualizado = (
        mapeamento.copy()
    )

    for indice, linha in (
        mapeamento_atualizado.iterrows()
    ):
        artista_id = limpar_texto(
            linha.get("artista_id")
        )

        nome_artista = limpar_texto(
            linha.get("nome_artista")
        )

        nome_esperado = limpar_texto(
            linha.get(
                "nome_spotify_esperado"
            )
        )

        nome_esperado_normalizado = (
            normalizar_texto(
                nome_esperado
            )
        )

        id_atual = limpar_texto(
            linha.get(
                "spotify_artista_id"
            )
        )

        nome_atual = limpar_texto(
            linha.get(
                "spotify_nome_artista"
            )
        )

        if id_atual:
            auditoria.append(
                {
                    "artista_id": artista_id,
                    "nome_artista": nome_artista,
                    "nome_spotify_esperado": (
                        nome_esperado
                    ),
                    "nome_esperado_normalizado": (
                        nome_esperado_normalizado
                    ),
                    "status": (
                        "já preenchido"
                    ),
                    "quantidade_ids_encontrados": 1,
                    "spotify_artista_id_encontrado": (
                        id_atual
                    ),
                    "spotify_nome_encontrado": (
                        nome_atual
                    ),
                    "fontes_encontradas": (
                        "mapeamento anterior"
                    ),
                }
            )

            continue

        candidatos = catalogo[
            catalogo[
                "spotify_nome_normalizado"
            ].eq(
                nome_esperado_normalizado
            )
        ].copy()

        ids_encontrados = sorted(
            candidatos[
                "spotify_artista_id"
            ].dropna().unique().tolist()
        )

        quantidade_ids = len(
            ids_encontrados
        )

        if quantidade_ids == 0:
            status = "não encontrado"
            id_encontrado = ""
            nome_encontrado = ""
            fontes_encontradas = ""

        elif quantidade_ids == 1:
            status = "preenchido automaticamente"
            id_encontrado = ids_encontrados[0]

            nomes = sorted(
                candidatos.loc[
                    candidatos[
                        "spotify_artista_id"
                    ].eq(
                        id_encontrado
                    ),
                    "spotify_nome_artista",
                ]
                .dropna()
                .unique()
                .tolist()
            )

            nome_encontrado = (
                nomes[0]
                if nomes
                else nome_esperado
            )

            fontes = sorted(
                candidatos.loc[
                    candidatos[
                        "spotify_artista_id"
                    ].eq(
                        id_encontrado
                    ),
                    "nome_fonte",
                ]
                .dropna()
                .unique()
                .tolist()
            )

            fontes_encontradas = (
                " | ".join(
                    fontes
                )
            )

            mapeamento_atualizado.at[
                indice,
                "spotify_artista_id",
            ] = id_encontrado

            mapeamento_atualizado.at[
                indice,
                "spotify_nome_artista",
            ] = nome_encontrado

        else:
            status = "ambíguo"
            id_encontrado = " | ".join(
                ids_encontrados
            )

            nomes = sorted(
                candidatos[
                    "spotify_nome_artista"
                ]
                .dropna()
                .unique()
                .tolist()
            )

            nome_encontrado = " | ".join(
                nomes
            )

            fontes = sorted(
                candidatos[
                    "nome_fonte"
                ]
                .dropna()
                .unique()
                .tolist()
            )

            fontes_encontradas = " | ".join(
                fontes
            )

        auditoria.append(
            {
                "artista_id": artista_id,
                "nome_artista": nome_artista,
                "nome_spotify_esperado": (
                    nome_esperado
                ),
                "nome_esperado_normalizado": (
                    nome_esperado_normalizado
                ),
                "status": status,
                "quantidade_ids_encontrados": (
                    quantidade_ids
                ),
                "spotify_artista_id_encontrado": (
                    id_encontrado
                ),
                "spotify_nome_encontrado": (
                    nome_encontrado
                ),
                "fontes_encontradas": (
                    fontes_encontradas
                ),
            }
        )

    auditoria = pd.DataFrame(
        auditoria
    )

    return (
        mapeamento_atualizado,
        auditoria,
    )


def validar_mapeamento(
    original,
    atualizado,
):
    if len(original) != len(atualizado):
        raise ValueError(
            "A quantidade de artistas foi "
            "alterada durante o mapeamento."
        )

    if atualizado[
        "artista_id"
    ].duplicated().any():
        raise ValueError(
            "Existem artista_id duplicados."
        )

    ids_preenchidos = atualizado[
        atualizado[
            "spotify_artista_id"
        ].apply(
            valor_preenchido
        )
    ].copy()

    duplicados_id = ids_preenchidos[
        ids_preenchidos[
            "spotify_artista_id"
        ].duplicated(
            keep=False
        )
    ]

    if not duplicados_id.empty:
        print(
            "\nALERTA: o mesmo ID do Spotify "
            "foi associado a mais de uma "
            "atração do festival:"
        )

        print(
            duplicados_id[
                [
                    "artista_id",
                    "nome_artista",
                    "spotify_artista_id",
                    "spotify_nome_artista",
                ]
            ].to_string(
                index=False
            )
        )


def main():
    print(
        "PREENCHENDO MAPEAMENTO "
        "DE ARTISTAS DO SPOTIFY"
    )

    if not ARQUIVO_MAPEAMENTO.exists():
        print(
            f"\nERRO: arquivo não encontrado: "
            f"{ARQUIVO_MAPEAMENTO}"
        )

        return

    try:
        mapeamento = pd.read_csv(
            ARQUIVO_MAPEAMENTO,
            encoding="utf-8-sig",
            dtype=str,
        ).fillna("")

        catalogo = construir_catalogo()

        (
            mapeamento_atualizado,
            auditoria,
        ) = procurar_correspondencias(
            mapeamento=mapeamento,
            catalogo=catalogo,
        )

        validar_mapeamento(
            original=mapeamento,
            atualizado=mapeamento_atualizado,
        )

    except ValueError as erro:
        print(
            f"\nERRO DE VALIDAÇÃO: {erro}"
        )

        return

    mapeamento_atualizado.to_csv(
        ARQUIVO_MAPEAMENTO,
        index=False,
        encoding="utf-8-sig",
    )

    auditoria.to_csv(
        ARQUIVO_AUDITORIA,
        index=False,
        encoding="utf-8-sig",
    )

    quantidade_preenchida = int(
        auditoria[
            "status"
        ].eq(
            "preenchido automaticamente"
        ).sum()
    )

    quantidade_anterior = int(
        auditoria[
            "status"
        ].eq(
            "já preenchido"
        ).sum()
    )

    quantidade_nao_encontrada = int(
        auditoria[
            "status"
        ].eq(
            "não encontrado"
        ).sum()
    )

    quantidade_ambigua = int(
        auditoria[
            "status"
        ].eq(
            "ambíguo"
        ).sum()
    )

    print(
        "\nMAPEAMENTO CONCLUÍDO"
    )

    print(
        f"Já preenchidos anteriormente: "
        f"{quantidade_anterior}"
    )

    print(
        f"Preenchidos automaticamente: "
        f"{quantidade_preenchida}"
    )

    print(
        f"Não encontrados: "
        f"{quantidade_nao_encontrada}"
    )

    print(
        f"Ambíguos: "
        f"{quantidade_ambigua}"
    )

    print(
        "\nResultado por artista:"
    )

    print(
        auditoria[
            [
                "nome_artista",
                "status",
                "spotify_nome_encontrado",
                "spotify_artista_id_encontrado",
            ]
        ].to_string(
            index=False
        )
    )

    print(
        f"\nMapeamento atualizado em: "
        f"{ARQUIVO_MAPEAMENTO}"
    )

    print(
        f"Auditoria salva em: "
        f"{ARQUIVO_AUDITORIA}"
    )


if __name__ == "__main__":
    main()