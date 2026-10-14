from difflib import SequenceMatcher
from hashlib import sha1
from pathlib import Path
import re
import unicodedata

import pandas as pd


PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_TRATADOS = PASTA_PROJETO / "dados" / "tratados"

ARQUIVO_VALIDADO = (
    PASTA_TRATADOS
    / "noticias_heineken_rir_validadas.csv"
)

ARQUIVO_PUBLICACOES = (
    PASTA_TRATADOS
    / "noticias_heineken_rir_publicacoes.csv"
)

ARQUIVO_PAUTAS = (
    PASTA_TRATADOS
    / "noticias_heineken_rir_pautas.csv"
)

ARQUIVO_SCROLLER = (
    PASTA_TRATADOS
    / "noticias_heineken_rir_scroller.csv"
)

ARQUIVO_VEICULOS = (
    PASTA_TRATADOS
    / "noticias_heineken_rir_veiculos.csv"
)

ARQUIVO_EVOLUCAO = (
    PASTA_TRATADOS
    / "noticias_heineken_rir_evolucao_diaria.csv"
)

ARQUIVO_INDICADORES = (
    PASTA_TRATADOS
    / "noticias_heineken_rir_indicadores.csv"
)

PALAVRAS_COMUNS = {
    "a", "ao", "as", "com", "da", "das", "de",
    "do", "dos", "e", "em", "no", "nos", "o",
    "os", "para", "por", "que", "um", "uma",
    "heineken", "rock", "rio", "brasil", "2026",
}


def limpar_texto(valor):
    if valor is None or pd.isna(valor):
        return ""

    texto = unicodedata.normalize(
        "NFKC",
        str(valor),
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto.strip()


def normalizar_texto(valor):
    texto = limpar_texto(valor)

    texto = unicodedata.normalize(
        "NFKD",
        texto,
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = texto.lower()

    texto = re.sub(
        r"[^a-z0-9]+",
        " ",
        texto,
    )

    return re.sub(
        r"\s+",
        " ",
        texto,
    ).strip()


def tokens_relevantes(texto):
    return {
        palavra
        for palavra in normalizar_texto(
            texto
        ).split()
        if (
            len(palavra) >= 3
            and palavra not in PALAVRAS_COMUNS
        )
    }


def categorias_da_linha(valor):
    return {
        limpar_texto(categoria)
        for categoria in str(valor).split("+")
        if limpar_texto(categoria)
    }


def similaridade_titulos(titulo_a, titulo_b):
    normalizado_a = normalizar_texto(
        titulo_a
    )
    normalizado_b = normalizar_texto(
        titulo_b
    )

    if normalizado_a == normalizado_b:
        return 1.0

    sequencia = SequenceMatcher(
        None,
        normalizado_a,
        normalizado_b,
    ).ratio()

    tokens_a = tokens_relevantes(
        titulo_a
    )
    tokens_b = tokens_relevantes(
        titulo_b
    )

    uniao = tokens_a | tokens_b

    if uniao:
        jaccard = len(
            tokens_a & tokens_b
        ) / len(uniao)
    else:
        jaccard = 0

    return max(
        sequencia,
        jaccard,
    )


def mesma_pauta(linha_a, linha_b):
    categorias_a = categorias_da_linha(
        linha_a["categoria_validada"]
    )
    categorias_b = categorias_da_linha(
        linha_b["categoria_validada"]
    )

    if not (
        categorias_a & categorias_b
    ):
        return False

    similaridade = similaridade_titulos(
        linha_a["titulo"],
        linha_b["titulo"],
    )

    return similaridade >= 0.82


def criar_pauta_id(titulos):
    bases = sorted(
        normalizar_texto(titulo)
        for titulo in titulos
    )

    base = bases[0] if bases else ""

    return "pauta_" + sha1(
        base.encode("utf-8")
    ).hexdigest()[:16]


def criar_clusters(publicacoes):
    quantidade = len(publicacoes)
    pais = list(range(quantidade))

    def encontrar(indice):
        while pais[indice] != indice:
            pais[indice] = pais[
                pais[indice]
            ]
            indice = pais[indice]

        return indice

    def unir(indice_a, indice_b):
        raiz_a = encontrar(indice_a)
        raiz_b = encontrar(indice_b)

        if raiz_a != raiz_b:
            pais[raiz_b] = raiz_a

    for indice_a in range(quantidade):
        linha_a = publicacoes.iloc[
            indice_a
        ]

        for indice_b in range(
            indice_a + 1,
            quantidade,
        ):
            linha_b = publicacoes.iloc[
                indice_b
            ]

            if mesma_pauta(
                linha_a,
                linha_b,
            ):
                unir(
                    indice_a,
                    indice_b,
                )

    grupos = {}

    for indice in range(quantidade):
        raiz = encontrar(indice)

        grupos.setdefault(
            raiz,
            [],
        ).append(indice)

    return list(grupos.values())


def escolher_representante(grupo):
    grupo = grupo.copy()

    grupo["tem_url"] = (
        grupo["url_final"]
        .fillna("")
        .str.strip()
        .ne("")
        .astype(int)
    )

    grupo["tem_lead"] = (
        grupo["lead_noticia"]
        .fillna("")
        .str.strip()
        .ne("")
        .astype(int)
    )

    grupo["tamanho_lead"] = (
        grupo["lead_noticia"]
        .fillna("")
        .str.len()
    )

    return (
        grupo
        .sort_values(
            [
                "tem_url",
                "tem_lead",
                "tamanho_lead",
                "data_publicacao_dt",
            ],
            ascending=[
                False,
                False,
                False,
                False,
            ],
        )
        .iloc[0]
    )


def preparar_publicacoes():
    if not ARQUIVO_VALIDADO.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: "
            f"{ARQUIVO_VALIDADO}"
        )

    dados = pd.read_csv(
        ARQUIVO_VALIDADO,
        encoding="utf-8-sig",
        dtype=str,
    ).fillna("")

    mascara_confirmada = (
        dados["status_validacao"]
        .eq("confirmada")
    )

    mascara_dashboard = (
        dados["incluir_dashboard"]
        .astype(str)
        .str.lower()
        .eq("true")
    )

    publicacoes = (
        dados[
            mascara_confirmada
            & mascara_dashboard
        ]
        .drop_duplicates(
            subset=["noticia_id"],
            keep="last",
        )
        .copy()
    )

    publicacoes[
        "data_publicacao_dt"
    ] = pd.to_datetime(
        publicacoes["data_publicacao"],
        errors="coerce",
        utc=True,
    )

    publicacoes["data"] = (
        publicacoes[
            "data_publicacao_dt"
        ]
        .dt.tz_convert(
            "America/Sao_Paulo"
        )
        .dt.date
        .astype(str)
    )

    return publicacoes


def gerar_pautas(publicacoes):
    clusters = criar_clusters(
        publicacoes
    )

    pautas = []
    publicacoes = publicacoes.copy()
    publicacoes["pauta_id"] = ""

    for cluster in clusters:
        grupo = publicacoes.iloc[
            cluster
        ].copy()

        pauta_id = criar_pauta_id(
            grupo["titulo"].tolist()
        )

        publicacoes.loc[
            publicacoes.index[cluster],
            "pauta_id",
        ] = pauta_id

        representante = (
            escolher_representante(
                grupo
            )
        )

        veiculos = sorted(
            {
                limpar_texto(veiculo)
                for veiculo
                in grupo["veiculo"]
                if limpar_texto(veiculo)
            }
        )

        categorias = sorted(
            {
                categoria
                for valor
                in grupo[
                    "categoria_validada"
                ]
                for categoria
                in categorias_da_linha(
                    valor
                )
            }
        )

        quantidade_publicacoes = (
            grupo["noticia_id"]
            .nunique()
        )

        quantidade_veiculos = (
            grupo["veiculo"]
            .nunique()
        )

        if quantidade_veiculos == 1:
            repercussao = "1 veículo"
        else:
            repercussao = (
                f"{quantidade_veiculos} "
                "veículos"
            )

        pautas.append(
            {
                "pauta_id": pauta_id,
                "titulo_representativo": (
                    representante["titulo"]
                ),
                "lead_representativo": (
                    representante[
                        "lead_noticia"
                    ]
                ),
                "veiculo_representativo": (
                    representante["veiculo"]
                ),
                "url_representativa": (
                    representante["url_final"]
                ),
                "categoria_validada": (
                    " + ".join(categorias)
                ),
                "primeira_publicacao": (
                    grupo[
                        "data_publicacao_dt"
                    ].min()
                ),
                "ultima_publicacao": (
                    grupo[
                        "data_publicacao_dt"
                    ].max()
                ),
                "quantidade_publicacoes": (
                    quantidade_publicacoes
                ),
                "quantidade_veiculos": (
                    quantidade_veiculos
                ),
                "repercussao": repercussao,
                "veiculos": (
                    " | ".join(veiculos)
                ),
            }
        )

    pautas_df = pd.DataFrame(
        pautas
    )

    pautas_df = (
        pautas_df
        .sort_values(
            "ultima_publicacao",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    return publicacoes, pautas_df


def gerar_scroller(pautas):
    scroller = pautas.copy()

    scroller["data"] = (
        pd.to_datetime(
            scroller[
                "ultima_publicacao"
            ],
            errors="coerce",
            utc=True,
        )
        .dt.tz_convert(
            "America/Sao_Paulo"
        )
        .dt.strftime("%d/%m/%Y")
    )

    scroller["texto_scroller"] = (
        scroller["data"]
        + " • "
        + scroller[
            "veiculo_representativo"
        ]
        + " — "
        + scroller[
            "titulo_representativo"
        ]
    )

    scroller["ordem_scroller"] = (
        range(
            1,
            len(scroller) + 1,
        )
    )

    return scroller[
        [
            "ordem_scroller",
            "pauta_id",
            "data",
            "texto_scroller",
            "titulo_representativo",
            "veiculo_representativo",
            "categoria_validada",
            "repercussao",
            "quantidade_veiculos",
            "url_representativa",
            "lead_representativo",
        ]
    ]


def gerar_veiculos(publicacoes):
    return (
        publicacoes
        .groupby(
            "veiculo",
            as_index=False,
        )
        .agg(
            quantidade_publicacoes=(
                "noticia_id",
                "nunique",
            ),
            quantidade_pautas=(
                "pauta_id",
                "nunique",
            ),
            primeira_publicacao=(
                "data",
                "min",
            ),
            ultima_publicacao=(
                "data",
                "max",
            ),
        )
        .sort_values(
            [
                "quantidade_publicacoes",
                "quantidade_pautas",
            ],
            ascending=False,
        )
        .reset_index(drop=True)
    )


def gerar_evolucao(publicacoes):
    evolucao = (
        publicacoes
        .groupby(
            "data",
            as_index=False,
        )
        .agg(
            quantidade_publicacoes=(
                "noticia_id",
                "nunique",
            ),
            quantidade_pautas=(
                "pauta_id",
                "nunique",
            ),
            quantidade_veiculos=(
                "veiculo",
                "nunique",
            ),
        )
        .sort_values("data")
    )

    evolucao[
        "media_movel_7_dias"
    ] = (
        evolucao[
            "quantidade_publicacoes"
        ]
        .rolling(
            window=7,
            min_periods=1,
        )
        .mean()
        .round(2)
    )

    return evolucao


def gerar_indicadores(
    publicacoes,
    pautas,
):
    categorias = publicacoes[
        "categoria_validada"
    ].fillna("")

    return pd.DataFrame(
        [
            {
                "publicacoes_confirmadas": (
                    publicacoes[
                        "noticia_id"
                    ].nunique()
                ),
                "pautas_distintas": (
                    pautas[
                        "pauta_id"
                    ].nunique()
                ),
                "veiculos_distintos": (
                    publicacoes[
                        "veiculo"
                    ].nunique()
                ),
                "publicacoes_rock_in_rio": (
                    categorias
                    .str.contains(
                        "Rock in Rio 2026",
                        regex=False,
                    )
                    .sum()
                ),
                "publicacoes_ultimate": (
                    categorias
                    .str.contains(
                        "Heineken Ultimate",
                        regex=False,
                    )
                    .sum()
                ),
                "publicacoes_heineken_zero": (
                    categorias
                    .str.contains(
                        "Heineken 0.0",
                        regex=False,
                    )
                    .sum()
                ),
                "primeira_publicacao": (
                    publicacoes[
                        "data_publicacao_dt"
                    ].min()
                ),
                "ultima_publicacao": (
                    publicacoes[
                        "data_publicacao_dt"
                    ].max()
                ),
            }
        ]
    )


def main():
    print(
        "PREPARANDO NOTÍCIAS PARA O DASHBOARD"
    )

    publicacoes = preparar_publicacoes()

    (
        publicacoes,
        pautas,
    ) = gerar_pautas(
        publicacoes
    )

    scroller = gerar_scroller(
        pautas
    )

    veiculos = gerar_veiculos(
        publicacoes
    )

    evolucao = gerar_evolucao(
        publicacoes
    )

    indicadores = gerar_indicadores(
        publicacoes,
        pautas,
    )

    publicacoes.drop(
        columns=[
            "data_publicacao_dt",
        ],
        errors="ignore",
    ).to_csv(
        ARQUIVO_PUBLICACOES,
        index=False,
        encoding="utf-8-sig",
    )

    pautas.to_csv(
        ARQUIVO_PAUTAS,
        index=False,
        encoding="utf-8-sig",
    )

    scroller.to_csv(
        ARQUIVO_SCROLLER,
        index=False,
        encoding="utf-8-sig",
    )

    veiculos.to_csv(
        ARQUIVO_VEICULOS,
        index=False,
        encoding="utf-8-sig",
    )

    evolucao.to_csv(
        ARQUIVO_EVOLUCAO,
        index=False,
        encoding="utf-8-sig",
    )

    indicadores.to_csv(
        ARQUIVO_INDICADORES,
        index=False,
        encoding="utf-8-sig",
    )

    maior_repercussao = (
        pautas
        .sort_values(
            "quantidade_veiculos",
            ascending=False,
        )
        .iloc[0]
    )

    print(
        "\nPREPARAÇÃO CONCLUÍDA"
    )
    print(
        f"Publicações confirmadas: "
        f"{len(publicacoes)}"
    )
    print(
        f"Pautas distintas: "
        f"{len(pautas)}"
    )
    print(
        f"Veículos distintos: "
        f"{publicacoes['veiculo'].nunique()}"
    )
    print(
        f"Registros no scroller: "
        f"{len(scroller)}"
    )

    print(
        "\nPauta com maior repercussão:"
    )
    print(
        f" - "
        f"{maior_repercussao['titulo_representativo']}"
    )
    print(
        f" - "
        f"{maior_repercussao['repercussao']}"
    )

    print(
        f"\nPublicações: "
        f"{ARQUIVO_PUBLICACOES}"
    )
    print(
        f"Pautas: {ARQUIVO_PAUTAS}"
    )
    print(
        f"Scroller: {ARQUIVO_SCROLLER}"
    )
    print(
        f"Veículos: {ARQUIVO_VEICULOS}"
    )
    print(
        f"Evolução: {ARQUIVO_EVOLUCAO}"
    )
    print(
        f"Indicadores: "
        f"{ARQUIVO_INDICADORES}"
    )


if __name__ == "__main__":
    main()