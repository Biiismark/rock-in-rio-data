from pathlib import Path

import pandas as pd


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

ARQUIVO_ARTISTAS = (
    PASTA_REFERENCIAS
    / "artistas.csv"
)

ARQUIVO_MAPEAMENTO = (
    PASTA_REFERENCIAS
    / "mapeamento_artistas_spotify.csv"
)

ARQUIVO_RANKING = (
    PASTA_TRATADOS
    / "spotify_ranking_diario.csv"
)

ARQUIVO_CREDITOS = (
    PASTA_TRATADOS
    / "spotify_creditos_diario.csv"
)

ARQUIVO_FAIXAS_RIR = (
    PASTA_TRATADOS
    / "spotify_rir_faixas_diario.csv"
)

ARQUIVO_STATUS_RIR = (
    PASTA_TRATADOS
    / "spotify_artistas_diario.csv"
)


def limpar_texto(valor):
    if valor is None or pd.isna(valor):
        return ""

    return str(valor).strip()


def carregar_csv(
    caminho,
    nome,
):
    if not caminho.exists():
        raise FileNotFoundError(
            f"{nome} não encontrado: "
            f"{caminho}"
        )

    dados = pd.read_csv(
        caminho,
        encoding="utf-8-sig",
        dtype={
            "artista_id": str,
            "spotify_artista_id": str,
            "artista_spotify_id": str,
            "faixa_id": str,
            "data_ranking": str,
        },
    )

    return dados


def carregar_arquivos():
    artistas = carregar_csv(
        ARQUIVO_ARTISTAS,
        "Cadastro de artistas",
    )

    mapeamento = carregar_csv(
        ARQUIVO_MAPEAMENTO,
        "Mapeamento do Spotify",
    )

    ranking = carregar_csv(
        ARQUIVO_RANKING,
        "Ranking diário do Spotify",
    )

    creditos = carregar_csv(
        ARQUIVO_CREDITOS,
        "Créditos do Spotify",
    )

    return (
        artistas,
        mapeamento,
        ranking,
        creditos,
    )


def validar_colunas(
    dados,
    colunas,
    nome,
):
    ausentes = (
        set(colunas)
        - set(dados.columns)
    )

    if ausentes:
        raise ValueError(
            f"{nome}: colunas ausentes: "
            + ", ".join(
                sorted(ausentes)
            )
        )


def validar_arquivos(
    artistas,
    mapeamento,
    ranking,
    creditos,
):
    validar_colunas(
        artistas,
        [
            "artista_id",
            "nome_artista",
            "nome_normalizado",
        ],
        "artistas.csv",
    )

    validar_colunas(
        mapeamento,
        [
            "artista_id",
            "nome_artista",
            "nome_spotify_esperado",
            "spotify_artista_id",
            "spotify_nome_artista",
        ],
        "mapeamento_artistas_spotify.csv",
    )

    validar_colunas(
        ranking,
        [
            "data_ranking",
            "faixa_id",
            "faixa",
            "posicao",
            "streams_dia",
            "streams_7_dias",
        ],
        "spotify_ranking_diario.csv",
    )

    validar_colunas(
        creditos,
        [
            "data_ranking",
            "faixa_id",
            "artista_spotify_id",
            "artista",
            "tipo_credito",
            "ordem_credito",
        ],
        "spotify_creditos_diario.csv",
    )

    if artistas[
        "artista_id"
    ].duplicated().any():
        raise ValueError(
            "Existem artista_id duplicados "
            "em artistas.csv."
        )

    if mapeamento[
        "artista_id"
    ].duplicated().any():
        raise ValueError(
            "Existem artista_id duplicados "
            "no mapeamento."
        )

    ids_vazios = (
        mapeamento[
            "spotify_artista_id"
        ]
        .fillna("")
        .astype(str)
        .str.strip()
        .isin(
            [
                "",
                "nan",
                "None",
            ]
        )
    )

    if ids_vazios.any():
        nomes = mapeamento.loc[
            ids_vazios,
            "nome_artista",
        ].tolist()

        raise ValueError(
            "Existem artistas sem ID do Spotify: "
            + " | ".join(nomes)
        )

    ids_invalidos = ~mapeamento[
        "spotify_artista_id"
    ].astype(str).str.fullmatch(
        r"[A-Za-z0-9]{22}"
    )

    if ids_invalidos.any():
        nomes = mapeamento.loc[
            ids_invalidos,
            "nome_artista",
        ].tolist()

        raise ValueError(
            "Existem IDs do Spotify inválidos: "
            + " | ".join(nomes)
        )

    ids_duplicados = mapeamento[
        "spotify_artista_id"
    ].duplicated(
        keep=False
    )

    if ids_duplicados.any():
        duplicados = mapeamento.loc[
            ids_duplicados,
            [
                "nome_artista",
                "spotify_artista_id",
            ],
        ]

        raise ValueError(
            "O mesmo ID está ligado a mais "
            "de uma atração:\n"
            + duplicados.to_string(
                index=False
            )
        )

    if len(mapeamento) != len(artistas):
        raise ValueError(
            "A quantidade de linhas do "
            "mapeamento é diferente do "
            "cadastro de artistas."
        )


def preparar_mapeamento(
    artistas,
    mapeamento,
):
    cadastro = artistas[
        [
            "artista_id",
            "nome_artista",
            "nome_normalizado",
        ]
    ].copy()

    colunas_mapeamento = (
        mapeamento[
            [
                "artista_id",
                "nome_spotify_esperado",
                "spotify_artista_id",
                "spotify_nome_artista",
            ]
        ]
        .copy()
    )

    resultado = cadastro.merge(
        colunas_mapeamento,
        on="artista_id",
        how="left",
        validate="one_to_one",
    )

    resultado[
        "spotify_artista_id"
    ] = (
        resultado[
            "spotify_artista_id"
        ]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    return resultado


def encontrar_faixas(
    mapeamento,
    ranking,
    creditos,
):
    creditos = creditos.copy()

    creditos[
        "artista_spotify_id"
    ] = (
        creditos[
            "artista_spotify_id"
        ]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    creditos_rir = creditos.merge(
        mapeamento[
            [
                "artista_id",
                "nome_artista",
                "spotify_artista_id",
                "spotify_nome_artista",
            ]
        ],
        left_on="artista_spotify_id",
        right_on="spotify_artista_id",
        how="inner",
        validate="many_to_one",
    )

    faixas_rir = creditos_rir.merge(
        ranking,
        on=[
            "data_ranking",
            "faixa_id",
        ],
        how="inner",
        suffixes=(
            "_credito",
            "_ranking",
        ),
        validate="many_to_one",
    )

    colunas_saida = [
        "data_ranking",
        "artista_id",
        "nome_artista",
        "spotify_artista_id",
        "spotify_nome_artista",
        "artista_spotify_id",
        "artista",
        "tipo_credito",
        "ordem_credito",
        "faixa_id",
        "faixa",
        "posicao",
        "movimento_posicao",
        "variacao_posicao",
        "dias_no_ranking",
        "pico",
        "vezes_no_pico",
        "streams_dia",
        "variacao_streams_dia",
        "streams_7_dias",
        "variacao_streams_7_dias",
        "streams_total",
        "pais",
        "plataforma",
        "url_fonte",
        "coletado_em",
    ]

    if faixas_rir.empty:
        return pd.DataFrame(
            columns=colunas_saida
        )

    faixas_rir = (
        faixas_rir[
            colunas_saida
        ]
        .drop_duplicates(
            subset=[
                "data_ranking",
                "artista_id",
                "faixa_id",
            ],
            keep="first",
        )
        .sort_values(
            [
                "data_ranking",
                "nome_artista",
                "posicao",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return faixas_rir


def criar_status_diario(
    mapeamento,
    ranking,
    faixas_rir,
):
    datas = pd.DataFrame(
        {
            "data_ranking": sorted(
                ranking[
                    "data_ranking"
                ]
                .dropna()
                .astype(str)
                .unique()
            )
        }
    )

    if datas.empty:
        raise ValueError(
            "Nenhuma data de ranking foi "
            "encontrada."
        )

    base_diaria = datas.merge(
        mapeamento,
        how="cross",
    )

    if faixas_rir.empty:
        resumo = pd.DataFrame(
            columns=[
                "data_ranking",
                "artista_id",
                "quantidade_faixas",
                "melhor_posicao",
                "streams_faixas_rankeadas",
                "streams_7_dias_faixas_rankeadas",
                "faixas_como_principal",
                "faixas_como_participacao",
            ]
        )

    else:
        resumo_geral = (
            faixas_rir
            .groupby(
                [
                    "data_ranking",
                    "artista_id",
                ],
                as_index=False,
            )
            .agg(
                quantidade_faixas=(
                    "faixa_id",
                    "nunique",
                ),
                melhor_posicao=(
                    "posicao",
                    "min",
                ),
                streams_faixas_rankeadas=(
                    "streams_dia",
                    "sum",
                ),
                streams_7_dias_faixas_rankeadas=(
                    "streams_7_dias",
                    "sum",
                ),
            )
        )

        resumo_creditos = (
            faixas_rir
            .assign(
                principal=(
                    faixas_rir[
                        "tipo_credito"
                    ].eq("principal")
                ).astype(int),
                participacao=(
                    faixas_rir[
                        "tipo_credito"
                    ].eq("participacao")
                ).astype(int),
            )
            .groupby(
                [
                    "data_ranking",
                    "artista_id",
                ],
                as_index=False,
            )
            .agg(
                faixas_como_principal=(
                    "principal",
                    "sum",
                ),
                faixas_como_participacao=(
                    "participacao",
                    "sum",
                ),
            )
        )

        resumo = resumo_geral.merge(
            resumo_creditos,
            on=[
                "data_ranking",
                "artista_id",
            ],
            how="left",
            validate="one_to_one",
        )

    status = base_diaria.merge(
        resumo,
        on=[
            "data_ranking",
            "artista_id",
        ],
        how="left",
        validate="one_to_one",
    )

    colunas_inteiras = [
        "quantidade_faixas",
        "streams_faixas_rankeadas",
        "streams_7_dias_faixas_rankeadas",
        "faixas_como_principal",
        "faixas_como_participacao",
    ]

    for coluna in colunas_inteiras:
        status[coluna] = (
            status[coluna]
            .fillna(0)
            .astype(int)
        )

    status[
        "presente_top_200"
    ] = (
        status[
            "quantidade_faixas"
        ] > 0
    )

    status = status[
        [
            "data_ranking",
            "artista_id",
            "nome_artista",
            "nome_normalizado",
            "nome_spotify_esperado",
            "spotify_artista_id",
            "spotify_nome_artista",
            "presente_top_200",
            "quantidade_faixas",
            "faixas_como_principal",
            "faixas_como_participacao",
            "melhor_posicao",
            "streams_faixas_rankeadas",
            "streams_7_dias_faixas_rankeadas",
        ]
    ]

    status = (
        status
        .sort_values(
            [
                "data_ranking",
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
    ranking,
    faixas_rir,
    status,
):
    quantidade_datas = (
        ranking[
            "data_ranking"
        ]
        .dropna()
        .nunique()
    )

    esperado_status = (
        quantidade_datas
        * len(mapeamento)
    )

    if len(status) != esperado_status:
        raise ValueError(
            "Quantidade inesperada no status: "
            f"{len(status)}. Esperado: "
            f"{esperado_status}."
        )

    if status[
        [
            "data_ranking",
            "artista_id",
        ]
    ].duplicated().any():
        raise ValueError(
            "Existem artistas duplicados "
            "na mesma data do status."
        )

    if not faixas_rir.empty:
        if faixas_rir[
            [
                "data_ranking",
                "artista_id",
                "faixa_id",
            ]
        ].duplicated().any():
            raise ValueError(
                "Existem faixas duplicadas "
                "para o mesmo artista e data."
            )

        ids_validos = set(
            mapeamento[
                "spotify_artista_id"
            ]
        )

        ids_encontrados = set(
            faixas_rir[
                "artista_spotify_id"
            ]
        )

        if not ids_encontrados.issubset(
            ids_validos
        ):
            raise ValueError(
                "O cruzamento produziu IDs "
                "que não pertencem ao festival."
            )


def salvar_resultados(
    faixas_rir,
    status,
):
    faixas_rir.to_csv(
        ARQUIVO_FAIXAS_RIR,
        index=False,
        encoding="utf-8-sig",
    )

    status.to_csv(
        ARQUIVO_STATUS_RIR,
        index=False,
        encoding="utf-8-sig",
    )


def mostrar_resultado(
    faixas_rir,
    status,
):
    data_mais_recente = (
        status[
            "data_ranking"
        ].max()
    )

    status_recente = status[
        status[
            "data_ranking"
        ].eq(
            data_mais_recente
        )
    ]

    encontrados = status_recente[
        status_recente[
            "presente_top_200"
        ]
    ]

    ausentes = status_recente[
        ~status_recente[
            "presente_top_200"
        ]
    ]

    print(
        "\nCRUZAMENTO CONCLUÍDO"
    )

    print(
        f"Data mais recente analisada: "
        f"{data_mais_recente}"
    )

    print(
        f"Datas acumuladas: "
        f"{status['data_ranking'].nunique()}"
    )

    print(
        "Artistas do festival no Top 200: "
        f"{len(encontrados)}"
    )

    print(
        "Artistas do festival fora do Top 200: "
        f"{len(ausentes)}"
    )

    if not encontrados.empty:
        print(
            "\nArtistas encontrados:"
        )

        for _, linha in encontrados.iterrows():
            melhor_posicao = int(
                linha[
                    "melhor_posicao"
                ]
            )

            print(
                f" - {linha['nome_artista']}: "
                f"{linha['quantidade_faixas']} "
                f"faixa(s), melhor posição "
                f"{melhor_posicao}, "
                f"{linha['faixas_como_principal']} "
                f"como principal e "
                f"{linha['faixas_como_participacao']} "
                f"como participação"
            )

    faixas_recentes = faixas_rir[
        faixas_rir[
            "data_ranking"
        ].eq(
            data_mais_recente
        )
    ]

    if not faixas_recentes.empty:
        print(
            "\nFaixas encontradas:"
        )

        for _, linha in (
            faixas_recentes.iterrows()
        ):
            print(
                f" - {linha['nome_artista']} | "
                f"{linha['faixa']} | "
                f"posição {int(linha['posicao'])} | "
                f"{int(linha['streams_dia']):,} "
                f"streams | "
                f"{linha['tipo_credito']}"
            )

    print(
        f"\nFaixas do festival: "
        f"{ARQUIVO_FAIXAS_RIR}"
    )

    print(
        f"Status diário: "
        f"{ARQUIVO_STATUS_RIR}"
    )

    print(
        "\nO arquivo de mapeamento não foi "
        "alterado pelo cruzamento."
    )


def main():
    print(
        "CRUZANDO SPOTIFY BRASIL "
        "COM O ROCK IN RIO 2026"
    )

    try:
        (
            artistas,
            mapeamento_original,
            ranking,
            creditos,
        ) = carregar_arquivos()

        validar_arquivos(
            artistas=artistas,
            mapeamento=mapeamento_original,
            ranking=ranking,
            creditos=creditos,
        )

        mapeamento = preparar_mapeamento(
            artistas=artistas,
            mapeamento=mapeamento_original,
        )

        faixas_rir = encontrar_faixas(
            mapeamento=mapeamento,
            ranking=ranking,
            creditos=creditos,
        )

        status = criar_status_diario(
            mapeamento=mapeamento,
            ranking=ranking,
            faixas_rir=faixas_rir,
        )

        validar_resultados(
            mapeamento=mapeamento,
            ranking=ranking,
            faixas_rir=faixas_rir,
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
        faixas_rir=faixas_rir,
        status=status,
    )

    mostrar_resultado(
        faixas_rir=faixas_rir,
        status=status,
    )


if __name__ == "__main__":
    main()