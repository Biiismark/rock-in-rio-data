from pathlib import Path

import pandas as pd


PASTA_PROJETO = (
    Path(__file__).resolve().parents[1]
)

ARQUIVO_MAPEAMENTO = (
    PASTA_PROJETO
    / "dados"
    / "referencias"
    / "mapeamento_artistas_spotify.csv"
)

ARQUIVO_AUDITORIA = (
    PASTA_PROJETO
    / "dados"
    / "referencias"
    / "auditoria_mapeamento_spotify_completo.csv"
)


MAPEAMENTO_VERIFICADO = {
    "art_the_hives": {
        "spotify_artista_id": (
            "4DToQR3aKrHQSSRzSz8Nzt"
        ),
        "spotify_nome_artista": (
            "The Hives"
        ),
    },
    "art_nova_twins": {
        "spotify_artista_id": (
            "7I95CM75shzCjHuTzrepjM"
        ),
        "spotify_nome_artista": (
            "Nova Twins"
        ),
    },
    "art_sepultura": {
        "spotify_artista_id": (
            "6JW8wliOEwaDZ231ZY7cf4"
        ),
        "spotify_nome_artista": (
            "Sepultura"
        ),
    },
    (
        "art_barao_vermelho_encontro_"
        "formacao_original_convida_"
        "fernando_magalhaes"
    ): {
        "spotify_artista_id": (
            "5zq0SGWxrmzpTSXkBEQzMj"
        ),
        "spotify_nome_artista": (
            "Barão Vermelho"
        ),
    },
    "art_gilberto_gil": {
        "spotify_artista_id": (
            "7oEkUINVIj1Nr3Wnj8tzqr"
        ),
        "spotify_nome_artista": (
            "Gilberto Gil"
        ),
    },
    "art_jon_batiste": {
        "spotify_artista_id": (
            "0eRbECAGCLLiTyVXPBRexU"
        ),
        "spotify_nome_artista": (
            "Jon Batiste"
        ),
    },
    "art_nexz": {
        "spotify_artista_id": (
            "5TaK8pOYVARAr5cdgoa8EW"
        ),
        "spotify_nome_artista": (
            "NEXZ"
        ),
    },
}


def validar_arquivo(dados):
    colunas_necessarias = {
        "artista_id",
        "nome_artista",
        "nome_normalizado",
        "nome_spotify_esperado",
        "spotify_artista_id",
        "spotify_nome_artista",
    }

    colunas_ausentes = (
        colunas_necessarias
        - set(dados.columns)
    )

    if colunas_ausentes:
        raise ValueError(
            "Colunas ausentes: "
            + ", ".join(
                sorted(
                    colunas_ausentes
                )
            )
        )

    if dados[
        "artista_id"
    ].duplicated().any():
        raise ValueError(
            "Existem artista_id duplicados."
        )


def preencher_mapeamento(dados):
    resultado = dados.copy()
    auditoria = []

    for (
        artista_id,
        identificacao,
    ) in MAPEAMENTO_VERIFICADO.items():
        mascara = resultado[
            "artista_id"
        ].eq(
            artista_id
        )

        quantidade = int(
            mascara.sum()
        )

        if quantidade != 1:
            raise ValueError(
                f"O artista_id {artista_id} "
                f"apareceu {quantidade} vezes."
            )

        linha = resultado[
            mascara
        ].iloc[0]

        id_anterior = str(
            linha.get(
                "spotify_artista_id",
                "",
            )
        ).strip()

        if id_anterior.lower() == "nan":
            id_anterior = ""

        id_verificado = identificacao[
            "spotify_artista_id"
        ]

        nome_verificado = identificacao[
            "spotify_nome_artista"
        ]

        if (
            id_anterior
            and id_anterior != id_verificado
        ):
            raise ValueError(
                f"Conflito para {artista_id}: "
                f"ID existente {id_anterior} e "
                f"ID verificado {id_verificado}."
            )

        resultado.loc[
            mascara,
            "spotify_artista_id",
        ] = id_verificado

        resultado.loc[
            mascara,
            "spotify_nome_artista",
        ] = nome_verificado

        auditoria.append(
            {
                "artista_id": artista_id,
                "nome_artista": (
                    linha["nome_artista"]
                ),
                "spotify_nome_artista": (
                    nome_verificado
                ),
                "spotify_artista_id": (
                    id_verificado
                ),
                "origem_validacao": (
                    "Página pública do Spotify"
                ),
                "status": "verificado",
            }
        )

    return (
        resultado,
        pd.DataFrame(
            auditoria
        ),
    )


def validar_resultado(dados):
    ids_vazios = (
        dados[
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

    quantidade_vazios = int(
        ids_vazios.sum()
    )

    if quantidade_vazios:
        artistas_vazios = dados.loc[
            ids_vazios,
            "nome_artista",
        ].tolist()

        raise ValueError(
            "Ainda existem artistas sem ID: "
            + " | ".join(
                artistas_vazios
            )
        )

    ids_invalidos = ~dados[
        "spotify_artista_id"
    ].astype(str).str.fullmatch(
        r"[A-Za-z0-9]{22}"
    )

    if ids_invalidos.any():
        artistas_invalidos = dados.loc[
            ids_invalidos,
            "nome_artista",
        ].tolist()

        raise ValueError(
            "Existem IDs em formato inválido: "
            + " | ".join(
                artistas_invalidos
            )
        )

    if dados[
        "spotify_artista_id"
    ].duplicated().any():
        duplicados = dados[
            dados[
                "spotify_artista_id"
            ].duplicated(
                keep=False
            )
        ]

        raise ValueError(
            "O mesmo ID foi associado a mais "
            "de uma atração:\n"
            + duplicados[
                [
                    "nome_artista",
                    "spotify_artista_id",
                ]
            ].to_string(
                index=False
            )
        )


def main():
    print(
        "COMPLETANDO MAPEAMENTO "
        "DOS ARTISTAS DO SPOTIFY"
    )

    if not ARQUIVO_MAPEAMENTO.exists():
        print(
            f"\nERRO: arquivo não encontrado: "
            f"{ARQUIVO_MAPEAMENTO}"
        )

        return

    try:
        dados = pd.read_csv(
            ARQUIVO_MAPEAMENTO,
            encoding="utf-8-sig",
            dtype=str,
        )

        validar_arquivo(
            dados
        )

        (
            resultado,
            auditoria,
        ) = preencher_mapeamento(
            dados
        )

        validar_resultado(
            resultado
        )

    except ValueError as erro:
        print(
            f"\nERRO DE VALIDAÇÃO: {erro}"
        )

        return

    resultado.to_csv(
        ARQUIVO_MAPEAMENTO,
        index=False,
        encoding="utf-8-sig",
    )

    auditoria.to_csv(
        ARQUIVO_AUDITORIA,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        "\nMAPEAMENTO COMPLETO"
    )

    print(
        f"Artistas cadastrados: "
        f"{len(resultado)}"
    )

    print(
        "Artistas com ID do Spotify: "
        f"{resultado['spotify_artista_id'].notna().sum()}"
    )

    print(
        "IDs únicos do Spotify: "
        f"{resultado['spotify_artista_id'].nunique()}"
    )

    print(
        "\nArtistas adicionados nesta etapa:"
    )

    print(
        auditoria[
            [
                "nome_artista",
                "spotify_nome_artista",
                "spotify_artista_id",
                "status",
            ]
        ].to_string(
            index=False
        )
    )

    print(
        f"\nMapeamento salvo em: "
        f"{ARQUIVO_MAPEAMENTO}"
    )

    print(
        f"Auditoria salva em: "
        f"{ARQUIVO_AUDITORIA}"
    )


if __name__ == "__main__":
    main()