from pathlib import Path

import pandas as pd


PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_REFERENCIAS = PASTA_PROJETO / "dados" / "referencias"
PASTA_TRATADOS = PASTA_PROJETO / "dados" / "tratados"

ARQUIVO_ENTRADA = PASTA_TRATADOS / "presenca_atual_rir_consolidada.csv"
ARQUIVO_ARTISTAS = PASTA_REFERENCIAS / "artistas.csv"

ARQUIVO_PRESENCA_ATUAL = PASTA_TRATADOS / "presenca_atual_rir_metricas.csv"
ARQUIVO_EVOLUCAO = PASTA_TRATADOS / "evolucao_presenca_rir.csv"
ARQUIVO_RESUMO = PASTA_TRATADOS / "resumo_presenca_rir_artistas.csv"


# Quantidade total de posições publicada por cada ranking.
# As páginas individuais são apenas complementares e usam o tamanho
# conhecido do ranking indicado pela plataforma e pelo tipo de item.
TAMANHOS_RANKING = {
    "itunes_musicas": 200,
    "itunes_albuns": 200,
    "apple_music_musicas": 200,
    "apple_music_albuns": 200,
    "shazam_musicas": 200,
    "deezer_musicas": 100,
    "youtube_diario": 20,
    "youtube_semanal": 100,
    "spotify_ranking_diario": 200,
}

TAMANHOS_COMPLEMENTOS = {
    ("Apple Music", "Música"): 200,
    ("Apple Music", "Álbum"): 200,
    ("Deezer", "Música"): 100,
    ("Shazam", "Música"): 200,
    ("Spotify", "Música"): 200,
    ("Spotify", "Álbum"): 200,
    ("iTunes", "Música"): 200,
    ("iTunes", "Álbum"): 200,
    ("YouTube", "Música/Vídeo"): 100,
}


def ler_csv(caminho):
    return pd.read_csv(
        caminho,
        encoding="utf-8-sig",
        dtype={
            "data_referencia": str,
            "artista_id": str,
            "registro_id": str,
        },
    )


def validar_colunas(dados):
    obrigatorias = {
        "data_referencia",
        "artista_id",
        "nome_artista",
        "plataforma",
        "tipo_item",
        "periodicidade",
        "titulo",
        "posicao",
        "fonte",
        "origem_registro",
        "prioridade_fonte",
        "data_plataforma_confirmada",
        "registro_id",
    }

    ausentes = sorted(obrigatorias - set(dados.columns))

    if ausentes:
        raise ValueError(
            "A base consolidada não possui estas colunas: "
            + ", ".join(ausentes)
        )


def converter_booleano(valor):
    if isinstance(valor, bool):
        return valor

    return str(valor).strip().lower() in {
        "true",
        "1",
        "sim",
        "yes",
    }


def obter_tamanho_ranking(linha):
    fonte = str(linha["fonte"])

    if fonte in TAMANHOS_RANKING:
        return TAMANHOS_RANKING[fonte]

    chave = (
        str(linha["plataforma"]),
        str(linha["tipo_item"]),
    )

    tamanho = TAMANHOS_COMPLEMENTOS.get(chave)

    if tamanho is None:
        raise ValueError(
            "Tamanho do ranking não configurado para: "
            f"fonte={fonte}, plataforma={chave[0]}, "
            f"tipo_item={chave[1]}"
        )

    return tamanho


def calcular_score_posicao(posicao, tamanho_ranking):
    posicao = int(posicao)
    tamanho_ranking = int(tamanho_ranking)

    if posicao < 1 or posicao > tamanho_ranking:
        raise ValueError(
            f"Posição {posicao} fora do ranking de "
            f"{tamanho_ranking} posições."
        )

    if tamanho_ranking == 1:
        return 100.0

    score = (
        (tamanho_ranking - posicao)
        / (tamanho_ranking - 1)
        * 100
    )

    return round(score, 2)


def classificar_faixa_score(score):
    if score >= 75:
        return "Quartil superior"

    if score >= 50:
        return "Segundo quartil"

    if score >= 25:
        return "Terceiro quartil"

    return "Quartil inferior"


def adicionar_metricas(dados):
    resultado = dados.copy()

    resultado["data_referencia"] = pd.to_datetime(
        resultado["data_referencia"],
        errors="raise",
    )

    resultado["posicao"] = pd.to_numeric(
        resultado["posicao"],
        errors="raise",
    ).astype(int)

    resultado["data_plataforma_confirmada"] = (
        resultado["data_plataforma_confirmada"]
        .map(converter_booleano)
        .astype(bool)
    )

    resultado["tamanho_ranking"] = resultado.apply(
        obter_tamanho_ranking,
        axis=1,
    )

    resultado["score_posicao"] = resultado.apply(
        lambda linha: calcular_score_posicao(
            linha["posicao"],
            linha["tamanho_ranking"],
        ),
        axis=1,
    )

    resultado["percentual_ranking_superado"] = (
        resultado["score_posicao"] / 100
    ).round(4)

    resultado["faixa_score"] = resultado[
        "score_posicao"
    ].map(classificar_faixa_score)

    resultado["elegivel_evolucao_diaria"] = resultado[
        "data_plataforma_confirmada"
    ]

    return resultado


def criar_presenca_atual(dados):
    diretos = dados[
        dados["data_plataforma_confirmada"]
    ].copy()

    complementos = dados[
        ~dados["data_plataforma_confirmada"]
    ].copy()

    if diretos.empty:
        atuais_diretos = diretos.copy()

    else:
        ultimas_datas = (
            diretos
            .groupby("fonte", as_index=False)["data_referencia"]
            .max()
            .rename(
                columns={
                    "data_referencia": "ultima_data_fonte"
                }
            )
        )

        atuais_diretos = diretos.merge(
            ultimas_datas,
            on="fonte",
            how="inner",
        )

        atuais_diretos = atuais_diretos[
            atuais_diretos["data_referencia"]
            == atuais_diretos["ultima_data_fonte"]
        ].drop(columns=["ultima_data_fonte"])

    atuais = pd.concat(
        [atuais_diretos, complementos],
        ignore_index=True,
    )

    atuais["fotografia_atual"] = True

    atuais = (
        atuais
        .sort_values(
            [
                "nome_artista",
                "plataforma",
                "tipo_item",
                "prioridade_fonte",
                "posicao",
                "titulo",
            ]
        )
        .reset_index(drop=True)
    )

    return atuais


def criar_evolucao(dados):
    evolucao = dados[
        dados["data_plataforma_confirmada"]
    ].copy()

    evolucao = (
        evolucao
        .sort_values(
            [
                "data_referencia",
                "fonte",
                "nome_artista",
                "posicao",
            ]
        )
        .reset_index(drop=True)
    )

    return evolucao


def juntar_textos_unicos(serie):
    valores = sorted(
        {
            str(valor).strip()
            for valor in serie.dropna()
            if str(valor).strip()
        }
    )

    return " | ".join(valores)


def criar_resumo_artistas(presenca_atual):
    artistas = pd.read_csv(
        ARQUIVO_ARTISTAS,
        encoding="utf-8-sig",
        dtype={"artista_id": str},
    )

    colunas_artistas = [
        coluna
        for coluna in [
            "artista_id",
            "nome_artista",
            "nome_normalizado",
            "genero",
            "pais",
            "foto_url",
            "bio_curta",
            "url_pagina_artista",
        ]
        if coluna in artistas.columns
    ]

    artistas = artistas[colunas_artistas].drop_duplicates(
        subset=["artista_id"],
        keep="last",
    )

    if presenca_atual.empty:
        resumo_metricas = pd.DataFrame(
            columns=["artista_id"]
        )

    else:
        resumo_metricas = (
            presenca_atual
            .groupby("artista_id", as_index=False)
            .agg(
                itens_em_charts=("registro_id", "nunique"),
                plataformas_com_presenca=(
                    "plataforma",
                    "nunique",
                ),
                fontes_com_presenca=("fonte", "nunique"),
                melhor_score_posicao=("score_posicao", "max"),
                score_medio_itens=("score_posicao", "mean"),
                melhor_posicao_bruta=("posicao", "min"),
                itens_coleta_direta=(
                    "data_plataforma_confirmada",
                    "sum",
                ),
                plataformas=(
                    "plataforma",
                    juntar_textos_unicos,
                ),
                tipos_item=(
                    "tipo_item",
                    juntar_textos_unicos,
                ),
                data_mais_recente=("data_referencia", "max"),
            )
        )

    resumo = artistas.merge(
        resumo_metricas,
        on="artista_id",
        how="left",
    )

    colunas_inteiras = [
        "itens_em_charts",
        "plataformas_com_presenca",
        "fontes_com_presenca",
        "melhor_posicao_bruta",
        "itens_coleta_direta",
    ]

    for coluna in colunas_inteiras:
        if coluna not in resumo.columns:
            resumo[coluna] = 0

        resumo[coluna] = (
            pd.to_numeric(resumo[coluna], errors="coerce")
            .fillna(0)
            .astype(int)
        )

    for coluna in [
        "melhor_score_posicao",
        "score_medio_itens",
    ]:
        if coluna not in resumo.columns:
            resumo[coluna] = 0.0

        resumo[coluna] = (
            pd.to_numeric(resumo[coluna], errors="coerce")
            .fillna(0)
            .round(2)
        )

    for coluna in ["plataformas", "tipos_item"]:
        if coluna not in resumo.columns:
            resumo[coluna] = ""

        resumo[coluna] = resumo[coluna].fillna("")

    resumo["tem_presenca_atual"] = (
        resumo["itens_em_charts"] > 0
    )

    resumo["tem_dado_direto_atual"] = (
        resumo["itens_coleta_direta"] > 0
    )

    resumo["somente_complemento_pagina"] = (
        resumo["tem_presenca_atual"]
        & ~resumo["tem_dado_direto_atual"]
    )

    resumo = (
        resumo
        .sort_values(
            [
                "tem_presenca_atual",
                "melhor_score_posicao",
                "plataformas_com_presenca",
                "nome_artista",
            ],
            ascending=[False, False, False, True],
        )
        .reset_index(drop=True)
    )

    resumo.insert(
        0,
        "ranking_presenca_atual",
        range(1, len(resumo) + 1),
    )

    resumo.loc[
        ~resumo["tem_presenca_atual"],
        "ranking_presenca_atual",
    ] = pd.NA

    resumo["ranking_presenca_atual"] = resumo[
        "ranking_presenca_atual"
    ].astype("Int64")

    return resumo


def salvar_csv(dados, caminho):
    dados_saida = dados.copy()

    if "data_referencia" in dados_saida.columns:
        dados_saida["data_referencia"] = (
            dados_saida["data_referencia"]
            .dt.strftime("%Y-%m-%d")
        )

    if "data_mais_recente" in dados_saida.columns:
        dados_saida["data_mais_recente"] = (
            pd.to_datetime(
                dados_saida["data_mais_recente"],
                errors="coerce",
            )
            .dt.strftime("%Y-%m-%d")
        )

    dados_saida.to_csv(
        caminho,
        index=False,
        encoding="utf-8-sig",
    )


def main():
    print(
        "CRIANDO MÉTRICAS DE PRESENÇA DOS ARTISTAS "
        "DO ROCK IN RIO"
    )

    if not ARQUIVO_ENTRADA.exists():
        raise FileNotFoundError(
            f"Base consolidada não encontrada: {ARQUIVO_ENTRADA}"
        )

    if not ARQUIVO_ARTISTAS.exists():
        raise FileNotFoundError(
            f"Cadastro de artistas não encontrado: {ARQUIVO_ARTISTAS}"
        )

    PASTA_TRATADOS.mkdir(parents=True, exist_ok=True)

    dados = ler_csv(ARQUIVO_ENTRADA)
    validar_colunas(dados)

    if dados.empty:
        raise ValueError("A base consolidada está vazia.")

    dados_metricas = adicionar_metricas(dados)
    presenca_atual = criar_presenca_atual(dados_metricas)
    evolucao = criar_evolucao(dados_metricas)
    resumo = criar_resumo_artistas(presenca_atual)

    salvar_csv(presenca_atual, ARQUIVO_PRESENCA_ATUAL)
    salvar_csv(evolucao, ARQUIVO_EVOLUCAO)
    salvar_csv(resumo, ARQUIVO_RESUMO)

    artistas_com_presenca = int(
        resumo["tem_presenca_atual"].sum()
    )

    artistas_sem_presenca = int(
        (~resumo["tem_presenca_atual"]).sum()
    )

    complementos_atuais = int(
        (~presenca_atual["data_plataforma_confirmada"]).sum()
    )

    print("\nMÉTRICAS CONCLUÍDAS")
    print(
        f"Registros da fotografia atual: {len(presenca_atual)}"
    )
    print(
        f"Registros na evolução confirmada: {len(evolucao)}"
    )
    print(f"Artistas analisados: {len(resumo)}")
    print(
        f"Artistas com presença atual: {artistas_com_presenca}"
    )
    print(
        f"Artistas sem presença atual: {artistas_sem_presenca}"
    )
    print(
        f"Complementos sem data de plataforma: {complementos_atuais}"
    )

    print("\nTamanhos dos rankings utilizados:")

    tamanhos = (
        presenca_atual[
            [
                "plataforma",
                "tipo_item",
                "periodicidade",
                "tamanho_ranking",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            [
                "plataforma",
                "tipo_item",
                "periodicidade",
            ]
        )
    )

    print(tamanhos.to_string(index=False))

    print(f"\nFotografia atual: {ARQUIVO_PRESENCA_ATUAL}")
    print(f"Evolução confirmada: {ARQUIVO_EVOLUCAO}")
    print(f"Resumo dos artistas: {ARQUIVO_RESUMO}")

    print(
        "\nNOTA: score_posicao compara a posição relativa dentro "
        "de cada ranking. Ele não representa audiência, receita "
        "ou impacto financeiro."
    )


if __name__ == "__main__":
    main()
