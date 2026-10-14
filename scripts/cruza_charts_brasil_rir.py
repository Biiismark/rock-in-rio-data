from pathlib import Path
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

PASTA_TRATADOS = (
    PASTA_PROJETO
    / "dados"
    / "tratados"
)

ARQUIVO_MAPEAMENTO = (
    PASTA_REFERENCIAS
    / "mapeamento_artistas_spotify.csv"
)

ARQUIVO_CHARTS = (
    PASTA_TRATADOS
    / "charts_brasil_diario.csv"
)

ARQUIVO_ITENS_RIR = (
    PASTA_TRATADOS
    / "charts_brasil_rir_itens.csv"
)

ARQUIVO_STATUS_RIR = (
    PASTA_TRATADOS
    / "charts_brasil_rir_status.csv"
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


def carregar_arquivos():
    if not ARQUIVO_MAPEAMENTO.exists():
        raise FileNotFoundError(
            f"Mapeamento não encontrado: "
            f"{ARQUIVO_MAPEAMENTO}"
        )

    if not ARQUIVO_CHARTS.exists():
        raise FileNotFoundError(
            f"Charts não encontrados: "
            f"{ARQUIVO_CHARTS}"
        )

    mapeamento = pd.read_csv(
        ARQUIVO_MAPEAMENTO,
        encoding="utf-8-sig",
        dtype=str,
    )

    charts = pd.read_csv(
        ARQUIVO_CHARTS,
        encoding="utf-8-sig",
        dtype={
            "data_referencia": str,
            "item_id": str,
        },
    )

    return (
        mapeamento,
        charts,
    )


def validar_arquivos(
    mapeamento,
    charts,
):
    colunas_mapeamento = {
        "artista_id",
        "nome_artista",
        "nome_spotify_esperado",
        "spotify_nome_artista",
    }

    colunas_charts = {
        "data_referencia",
        "fonte",
        "plataforma",
        "tipo_item",
        "periodicidade",
        "item_id",
        "artista",
        "artista_normalizado",
        "titulo",
        "item_bruto",
        "posicao",
    }

    ausentes_mapeamento = (
        colunas_mapeamento
        - set(mapeamento.columns)
    )

    ausentes_charts = (
        colunas_charts
        - set(charts.columns)
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

    if ausentes_charts:
        raise ValueError(
            "Colunas ausentes nos charts: "
            + ", ".join(
                sorted(
                    ausentes_charts
                )
            )
        )

    if len(mapeamento) != 28:
        raise ValueError(
            "O mapeamento não contém "
            "os 28 artistas."
        )

    if mapeamento[
        "artista_id"
    ].duplicated().any():
        raise ValueError(
            "Existem artista_id duplicados."
        )

    if charts[
        [
            "data_referencia",
            "fonte",
            "item_id",
        ]
    ].duplicated().any():
        raise ValueError(
            "Existem itens duplicados no "
            "mesmo snapshot."
        )


def criar_aliases(
    mapeamento,
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

        for candidato in candidatos:
            alias_normalizado = (
                normalizar_texto(
                    candidato
                )
            )

            if not alias_normalizado:
                continue

            registros.append(
                {
                    "artista_id": artista_id,
                    "nome_artista": nome_artista,
                    "alias": candidato,
                    "alias_normalizado": (
                        alias_normalizado
                    ),
                }
            )

    aliases = pd.DataFrame(
        registros
    )

    aliases = (
        aliases
        .drop_duplicates(
            subset=[
                "artista_id",
                "alias_normalizado",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    ambiguos = (
        aliases
        .groupby(
            "alias_normalizado"
        )[
            "artista_id"
        ]
        .nunique()
    )

    ambiguos = ambiguos[
        ambiguos > 1
    ]

    if not ambiguos.empty:
        raise ValueError(
            "Existem aliases associados a "
            "mais de uma atração: "
            + " | ".join(
                ambiguos.index.tolist()
            )
        )

    return aliases


def encontrar_itens(
    charts,
    aliases,
):
    dados = charts.copy()

    dados[
        "artista_normalizado"
    ] = (
        dados[
            "artista_normalizado"
        ]
        .fillna("")
        .astype(str)
        .map(
            normalizar_texto
        )
    )

    encontrados = dados.merge(
        aliases,
        left_on="artista_normalizado",
        right_on="alias_normalizado",
        how="inner",
        validate="many_to_one",
    )

    encontrados[
        "metodo_correspondencia"
    ] = (
        "nome exato do artista principal"
    )

    colunas = [
        "data_referencia",
        "fonte",
        "plataforma",
        "pais",
        "tipo_item",
        "periodicidade",
        "artista_id",
        "nome_artista",
        "alias",
        "metodo_correspondencia",
        "item_id",
        "artista",
        "titulo",
        "item_bruto",
        "posicao",
        "movimento_posicao",
        "semanas_no_ranking",
        "pico",
        "vezes_no_pico",
        "valor_fonte",
        "variacao_valor_fonte",
        "tipo_data",
        "data_coleta",
        "coletado_em",
        "url_fonte",
    ]

    encontrados = (
        encontrados[
            colunas
        ]
        .drop_duplicates(
            subset=[
                "data_referencia",
                "fonte",
                "artista_id",
                "item_id",
            ]
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

    return encontrados


def criar_status(
    mapeamento,
    charts,
    encontrados,
):
    snapshots = (
        charts[
            [
                "data_referencia",
                "fonte",
                "plataforma",
                "tipo_item",
                "periodicidade",
            ]
        ]
        .drop_duplicates()
        .reset_index(
            drop=True
        )
    )

    artistas = mapeamento[
        [
            "artista_id",
            "nome_artista",
        ]
    ].copy()

    base = snapshots.merge(
        artistas,
        how="cross",
    )

    if encontrados.empty:
        resumo = pd.DataFrame(
            columns=[
                "data_referencia",
                "fonte",
                "artista_id",
                "quantidade_itens",
                "melhor_posicao",
                "valor_total_fonte",
            ]
        )

    else:
        resumo = (
            encontrados
            .groupby(
                [
                    "data_referencia",
                    "fonte",
                    "artista_id",
                ],
                as_index=False,
            )
            .agg(
                quantidade_itens=(
                    "item_id",
                    "nunique",
                ),
                melhor_posicao=(
                    "posicao",
                    "min",
                ),
                valor_total_fonte=(
                    "valor_fonte",
                    lambda coluna: (
                        coluna.sum(
                            min_count=1
                        )
                    ),
                ),
            )
        )

    status = base.merge(
        resumo,
        on=[
            "data_referencia",
            "fonte",
            "artista_id",
        ],
        how="left",
        validate="one_to_one",
    )

    status[
        "quantidade_itens"
    ] = (
        status[
            "quantidade_itens"
        ]
        .fillna(0)
        .astype(int)
    )

    status[
        "presente_no_ranking"
    ] = (
        status[
            "quantidade_itens"
        ] > 0
    )

    status = (
        status[
            [
                "data_referencia",
                "fonte",
                "plataforma",
                "tipo_item",
                "periodicidade",
                "artista_id",
                "nome_artista",
                "presente_no_ranking",
                "quantidade_itens",
                "melhor_posicao",
                "valor_total_fonte",
            ]
        ]
        .sort_values(
            [
                "data_referencia",
                "plataforma",
                "tipo_item",
                "nome_artista",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return status


def validar_resultados(
    mapeamento,
    charts,
    encontrados,
    status,
):
    snapshots = charts[
        [
            "data_referencia",
            "fonte",
        ]
    ].drop_duplicates()

    esperado = (
        len(snapshots)
        * len(mapeamento)
    )

    if len(status) != esperado:
        raise ValueError(
            f"Status com {len(status)} linhas. "
            f"Esperado: {esperado}."
        )

    if status[
        [
            "data_referencia",
            "fonte",
            "artista_id",
        ]
    ].duplicated().any():
        raise ValueError(
            "Existem artistas duplicados "
            "no mesmo snapshot."
        )

    if not encontrados.empty and encontrados[
        [
            "data_referencia",
            "fonte",
            "artista_id",
            "item_id",
        ]
    ].duplicated().any():
        raise ValueError(
            "Existem itens encontrados "
            "duplicados."
        )


def salvar_resultados(
    encontrados,
    status,
):
    encontrados.to_csv(
        ARQUIVO_ITENS_RIR,
        index=False,
        encoding="utf-8-sig",
    )

    status.to_csv(
        ARQUIVO_STATUS_RIR,
        index=False,
        encoding="utf-8-sig",
    )


def mostrar_resultado(
    encontrados,
    status,
):
    print(
        "\nCRUZAMENTO MULTIPLATAFORMA "
        "CONCLUÍDO"
    )

    print(
        f"Itens encontrados: "
        f"{len(encontrados)}"
    )

    artistas_encontrados = (
        encontrados[
            "artista_id"
        ].nunique()
        if not encontrados.empty
        else 0
    )

    print(
        f"Artistas encontrados: "
        f"{artistas_encontrados}"
    )

    resumo = (
        encontrados
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
                "item_id",
                "nunique",
            ),
            melhor_posicao=(
                "posicao",
                "min",
            ),
        )
        if not encontrados.empty
        else pd.DataFrame()
    )

    if not resumo.empty:
        print(
            "\nResultados:"
        )

        for _, linha in (
            resumo.iterrows()
        ):
            print(
                f" - {linha['plataforma']} | "
                f"{linha['tipo_item']} | "
                f"{linha['nome_artista']}: "
                f"{linha['quantidade']} item(ns), "
                f"melhor posição "
                f"{int(linha['melhor_posicao'])}"
            )

    print(
        f"\nItens encontrados: "
        f"{ARQUIVO_ITENS_RIR}"
    )

    print(
        f"Status por plataforma: "
        f"{ARQUIVO_STATUS_RIR}"
    )

    print(
        "\nLIMITAÇÃO: este cruzamento considera "
        "o artista principal informado pelo chart. "
        "Participações escritas apenas no título "
        "serão auditadas posteriormente pelas "
        "páginas individuais do Kworb."
    )


def main():
    print(
        "CRUZANDO CHARTS DO BRASIL "
        "COM O ROCK IN RIO 2026"
    )

    try:
        (
            mapeamento,
            charts,
        ) = carregar_arquivos()

        validar_arquivos(
            mapeamento=mapeamento,
            charts=charts,
        )

        aliases = criar_aliases(
            mapeamento
        )

        encontrados = encontrar_itens(
            charts=charts,
            aliases=aliases,
        )

        status = criar_status(
            mapeamento=mapeamento,
            charts=charts,
            encontrados=encontrados,
        )

        validar_resultados(
            mapeamento=mapeamento,
            charts=charts,
            encontrados=encontrados,
            status=status,
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
        encontrados=encontrados,
        status=status,
    )

    mostrar_resultado(
        encontrados=encontrados,
        status=status,
    )


if __name__ == "__main__":
    main()