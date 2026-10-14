from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd


FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")
DATA_INICIO_EVENTO = pd.Timestamp("2026-09-04")
DATA_FIM_EVENTO = pd.Timestamp("2026-09-13")

PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_REFERENCIAS = PASTA_PROJETO / "dados" / "referencias"
PASTA_TRATADOS = PASTA_PROJETO / "dados" / "tratados"

ARQUIVO_CALENDARIO = PASTA_TRATADOS / "dim_calendario.csv"
ARQUIVO_ARTISTAS_SAIDA = PASTA_TRATADOS / "dim_artistas.csv"
ARQUIVO_PLATAFORMAS = PASTA_TRATADOS / "dim_plataformas.csv"
ARQUIVO_CONTROLE = PASTA_TRATADOS / "controle_atualizacao_fontes.csv"


# Cada entrada aponta para uma tabela de fatos e para a data que deverá ser
# relacionada com dim_calendario[data]. Arquivos ausentes são registrados no
# controle, mas não impedem a criação das dimensões.
FONTES_DATA = [
    {
        "arquivo": "spotify_ranking_diario.csv",
        "coluna_data": "data_ranking",
        "nome_tabela": "fato_spotify_ranking",
        "grupo": "Spotify",
        "granularidade": "Diária",
    },
    {
        "arquivo": "charts_brasil_diario.csv",
        "coluna_data": "data_referencia",
        "nome_tabela": "fato_charts_brasil",
        "grupo": "Charts multiplataforma",
        "granularidade": "Mista por fonte",
    },
    {
        "arquivo": "evolucao_presenca_rir.csv",
        "coluna_data": "data_referencia",
        "nome_tabela": "fato_evolucao_presenca",
        "grupo": "Presença no Brasil",
        "granularidade": "Mista por fonte",
    },
    {
        "arquivo": "google_trends_rir_evolucao.csv",
        "coluna_data": "data",
        "nome_tabela": "fato_google_trends_evolucao",
        "grupo": "Google Trends",
        "granularidade": "Diária",
    },
]


MESES = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

DIAS_SEMANA = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}


def ler_datas(caminho, coluna):
    cabecalho = pd.read_csv(
        caminho,
        encoding="utf-8-sig",
        nrows=0,
    )

    if coluna not in cabecalho.columns:
        raise ValueError(
            f"A coluna {coluna!r} não existe em {caminho.name}."
        )

    dados = pd.read_csv(
        caminho,
        encoding="utf-8-sig",
        usecols=[coluna],
        dtype={coluna: str},
    )
    datas = pd.to_datetime(dados[coluna], errors="coerce").dropna()
    return datas.dt.normalize(), len(dados)


def fase_projeto(data):
    if data < DATA_INICIO_EVENTO:
        return "Pré-festival"
    if data <= DATA_FIM_EVENTO:
        return "Durante o festival"
    return "Pós-festival"


def criar_calendario(datas_encontradas):
    hoje = pd.Timestamp(datetime.now(FUSO_BRASIL).date())

    if datas_encontradas:
        inicio = min(serie.min() for serie in datas_encontradas)
        fim_dados = max(serie.max() for serie in datas_encontradas)
    else:
        inicio = hoje
        fim_dados = hoje

    fim = max(fim_dados, DATA_FIM_EVENTO)
    calendario = pd.DataFrame(
        {"data": pd.date_range(inicio, fim, freq="D")}
    )

    calendario["data_id"] = calendario["data"].dt.strftime("%Y%m%d").astype(int)
    calendario["ano"] = calendario["data"].dt.year
    calendario["mes_numero"] = calendario["data"].dt.month
    calendario["mes_nome"] = calendario["mes_numero"].map(MESES)
    calendario["ano_mes"] = calendario["data"].dt.strftime("%Y-%m")
    calendario["ano_mes_ordem"] = (
        calendario["ano"] * 100 + calendario["mes_numero"]
    )
    calendario["dia"] = calendario["data"].dt.day
    calendario["dia_semana_numero"] = calendario["data"].dt.weekday + 1
    calendario["dia_semana_nome"] = (
        calendario["data"].dt.weekday.map(DIAS_SEMANA)
    )
    calendario["fim_de_semana"] = calendario["data"].dt.weekday >= 5
    calendario["data_formatada"] = calendario["data"].dt.strftime("%d/%m/%Y")
    calendario["fase_projeto"] = calendario["data"].map(fase_projeto)
    calendario["dia_de_show"] = calendario["data"].isin(
        pd.date_range(DATA_INICIO_EVENTO, DATA_FIM_EVENTO, freq="D")
    )
    calendario["dias_ate_inicio_festival"] = (
        DATA_INICIO_EVENTO - calendario["data"]
    ).dt.days
    calendario["data_com_dados"] = calendario["data"] <= fim_dados
    calendario["data_futura"] = calendario["data"] > hoje
    calendario["ultima_data_disponivel"] = calendario["data"] == fim_dados

    return calendario, inicio, fim, fim_dados


def criar_dim_artistas():
    entrada = PASTA_REFERENCIAS / "artistas.csv"

    if not entrada.exists():
        raise FileNotFoundError(f"Cadastro não encontrado: {entrada}")

    artistas = pd.read_csv(
        entrada,
        encoding="utf-8-sig",
        dtype={"artista_id": str},
    )

    obrigatorias = {"artista_id", "nome_artista"}
    ausentes = obrigatorias - set(artistas.columns)

    if ausentes:
        raise ValueError(
            "Colunas ausentes no cadastro de artistas: "
            + ", ".join(sorted(ausentes))
        )

    artistas = (
        artistas
        .drop_duplicates(subset=["artista_id"], keep="last")
        .sort_values("nome_artista")
        .reset_index(drop=True)
    )
    artistas["ordem_alfabetica"] = range(1, len(artistas) + 1)
    return artistas


def criar_dim_plataformas():
    registros = [
        ("Spotify", "Streaming", "Diária", True),
        ("Apple Music", "Streaming", "Snapshot diário", False),
        ("Deezer", "Streaming", "Snapshot diário", False),
        ("Shazam", "Descoberta", "Snapshot diário", False),
        ("iTunes", "Compra digital", "Snapshot diário", False),
        ("YouTube", "Vídeo", "Diária/Semanal", True),
        ("Google Trends", "Busca", "Diária", True),
    ]
    return pd.DataFrame(
        registros,
        columns=[
            "plataforma",
            "categoria_metrica",
            "periodicidade_padrao",
            "possui_serie_temporal_nativa",
        ],
    )


def main():
    PASTA_TRATADOS.mkdir(parents=True, exist_ok=True)
    agora = datetime.now(FUSO_BRASIL)
    datas_encontradas = []
    controle = []

    print("PREPARANDO MODELO TEMPORAL PARA O POWER BI")

    for fonte in FONTES_DATA:
        caminho = PASTA_TRATADOS / fonte["arquivo"]

        if not caminho.exists():
            controle.append(
                {
                    **fonte,
                    "status_arquivo": "ausente",
                    "registros": 0,
                    "primeira_data": pd.NaT,
                    "ultima_data": pd.NaT,
                    "datas_distintas": 0,
                    "atraso_dias": pd.NA,
                    "verificado_em": agora.isoformat(timespec="seconds"),
                }
            )
            print(f" - {fonte['arquivo']}: ausente")
            continue

        datas, registros = ler_datas(caminho, fonte["coluna_data"])

        if datas.empty:
            primeira = pd.NaT
            ultima = pd.NaT
            distintas = 0
            atraso = pd.NA
            status = "sem datas válidas"
        else:
            primeira = datas.min()
            ultima = datas.max()
            distintas = datas.nunique()
            atraso = (pd.Timestamp(agora.date()) - ultima).days
            status = "disponível"
            datas_encontradas.append(datas)

        controle.append(
            {
                **fonte,
                "status_arquivo": status,
                "registros": registros,
                "primeira_data": primeira,
                "ultima_data": ultima,
                "datas_distintas": distintas,
                "atraso_dias": atraso,
                "verificado_em": agora.isoformat(timespec="seconds"),
            }
        )
        print(
            f" - {fonte['arquivo']}: {registros} registros | "
            f"{distintas} data(s) | última: {ultima.date() if pd.notna(ultima) else '-'}"
        )

    calendario, inicio, fim, fim_dados = criar_calendario(datas_encontradas)
    artistas = criar_dim_artistas()
    plataformas = criar_dim_plataformas()
    controle_df = pd.DataFrame(controle)

    calendario.to_csv(ARQUIVO_CALENDARIO, index=False, encoding="utf-8-sig")
    artistas.to_csv(ARQUIVO_ARTISTAS_SAIDA, index=False, encoding="utf-8-sig")
    plataformas.to_csv(ARQUIVO_PLATAFORMAS, index=False, encoding="utf-8-sig")
    controle_df.to_csv(ARQUIVO_CONTROLE, index=False, encoding="utf-8-sig")

    print("\nMODELO TEMPORAL PREPARADO")
    print(f"Calendário: {inicio.date()} até {fim.date()}")
    print(f"Última data encontrada nas bases: {fim_dados.date()}")
    print(f"Datas no calendário: {len(calendario)}")
    print(f"Artistas na dimensão: {len(artistas)}")
    print(f"Plataformas/canais na dimensão: {len(plataformas)}")
    print(f"\nCalendário: {ARQUIVO_CALENDARIO}")
    print(f"Artistas: {ARQUIVO_ARTISTAS_SAIDA}")
    print(f"Plataformas: {ARQUIVO_PLATAFORMAS}")
    print(f"Controle das fontes: {ARQUIVO_CONTROLE}")
    print(
        "\nNo Power BI, use dim_calendario[data] no segmentador de data "
        "e relacione-a com a coluna de data indicada em controle_atualizacao_fontes.csv."
    )


if __name__ == "__main__":
    main()
