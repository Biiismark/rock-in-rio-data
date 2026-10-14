from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote
import json
import time

import pandas as pd
from pytrends.request import TrendReq


TERMOS = [
    "Rock in Rio",
    "Heineken",
    "Foo Fighters",
    "Stray Kids",
    "Pedro Sampaio",
]

PAIS = "BR"
CATEGORIA = 0
TIPO_PESQUISA = ""

PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_BRUTOS = PASTA_PROJETO / "dados" / "brutos" / "google_trends_teste"
PASTA_TRATADOS = PASTA_PROJETO / "dados" / "tratados"

ARQUIVO_EVOLUCAO = PASTA_TRATADOS / "google_trends_teste_evolucao.csv"
ARQUIVO_ESTADOS = PASTA_TRATADOS / "google_trends_teste_estados.csv"
ARQUIVO_PARAMETROS = PASTA_BRUTOS / "google_trends_teste_parametros.json"


def criar_cliente():
    # retries=0 evita incompatibilidade do pytrends arquivado
    # com versões recentes do urllib3. As tentativas são feitas
    # explicitamente por este script.
    return TrendReq(
        hl="pt-BR",
        tz=180,
        timeout=(10, 30),
        retries=0,
        backoff_factor=0,
    )


def executar_com_tentativas(funcao, descricao, tentativas=3):
    ultimo_erro = None

    for tentativa in range(1, tentativas + 1):
        try:
            return funcao()

        except Exception as erro:
            ultimo_erro = erro

            if tentativa == tentativas:
                break

            espera = 5 * tentativa
            print(
                f"   Falha em {descricao}: {erro}\n"
                f"   Nova tentativa em {espera} segundos..."
            )
            time.sleep(espera)

    raise RuntimeError(
        f"Não foi possível concluir {descricao}: {ultimo_erro}"
    ) from ultimo_erro


def montar_consulta(cliente, periodo):
    cliente.build_payload(
        kw_list=TERMOS,
        cat=CATEGORIA,
        timeframe=periodo,
        geo=PAIS,
        gprop=TIPO_PESQUISA,
    )


def tratar_evolucao(dados):
    if dados.empty:
        raise ValueError("O Google Trends não retornou evolução temporal.")

    resultado = dados.copy().reset_index()

    if "isPartial" in resultado.columns:
        resultado = resultado.drop(columns=["isPartial"])

    resultado = resultado.melt(
        id_vars=["date"],
        value_vars=TERMOS,
        var_name="termo",
        value_name="interesse_relativo",
    )

    resultado = resultado.rename(columns={"date": "data"})
    resultado["data"] = pd.to_datetime(resultado["data"])
    resultado["pais"] = "Brasil"
    resultado["geo"] = PAIS
    resultado["fonte"] = "Google Trends"

    return resultado[
        [
            "data",
            "termo",
            "interesse_relativo",
            "pais",
            "geo",
            "fonte",
        ]
    ]


def tratar_estados(dados):
    if dados.empty:
        return pd.DataFrame(
            columns=[
                "estado",
                "termo",
                "interesse_relativo",
                "pais",
                "geo",
                "fonte",
            ]
        )

    resultado = dados.copy().reset_index()

    coluna_regiao = resultado.columns[0]
    resultado = resultado.rename(columns={coluna_regiao: "estado"})

    resultado = resultado.melt(
        id_vars=["estado"],
        value_vars=TERMOS,
        var_name="termo",
        value_name="interesse_relativo",
    )

    resultado["pais"] = "Brasil"
    resultado["geo"] = PAIS
    resultado["fonte"] = "Google Trends"

    return resultado[
        [
            "estado",
            "termo",
            "interesse_relativo",
            "pais",
            "geo",
            "fonte",
        ]
    ]


def criar_url_validacao(data_inicio, data_fim):
    termos_url = ",".join(quote(termo) for termo in TERMOS)
    periodo_url = quote(f"{data_inicio} {data_fim}")

    return (
        "https://trends.google.com/trends/explore"
        f"?date={periodo_url}&geo={PAIS}&q={termos_url}"
    )


def main():
    print("TESTANDO GOOGLE TRENDS — BRASIL")

    data_fim = date.today()
    data_inicio = data_fim - timedelta(days=90)
    periodo = f"{data_inicio.isoformat()} {data_fim.isoformat()}"

    PASTA_BRUTOS.mkdir(parents=True, exist_ok=True)
    PASTA_TRATADOS.mkdir(parents=True, exist_ok=True)

    print(f"Período: {periodo}")
    print(f"País: {PAIS}")
    print("Termos:")

    for termo in TERMOS:
        print(f" - {termo}")

    def coletar_evolucao():
        cliente = criar_cliente()
        montar_consulta(cliente, periodo)
        return cliente.interest_over_time()

    print("\nColetando evolução temporal...")
    evolucao_bruta = executar_com_tentativas(
        coletar_evolucao,
        "evolução temporal",
    )

    # Pequena pausa reduz a chance de bloqueio entre as duas consultas.
    time.sleep(3)

    def coletar_estados():
        cliente = criar_cliente()
        montar_consulta(cliente, periodo)
        return cliente.interest_by_region(
            resolution="REGION",
            inc_low_vol=True,
            inc_geo_code=False,
        )

    print("Coletando interesse por estado...")
    estados_brutos = executar_com_tentativas(
        coletar_estados,
        "interesse por estado",
    )

    evolucao = tratar_evolucao(evolucao_bruta)
    estados = tratar_estados(estados_brutos)

    evolucao.to_csv(
        ARQUIVO_EVOLUCAO,
        index=False,
        encoding="utf-8-sig",
    )

    estados.to_csv(
        ARQUIVO_ESTADOS,
        index=False,
        encoding="utf-8-sig",
    )

    url_validacao = criar_url_validacao(data_inicio, data_fim)

    parametros = {
        "data_inicio": data_inicio.isoformat(),
        "data_fim": data_fim.isoformat(),
        "periodo": periodo,
        "geo": PAIS,
        "pais": "Brasil",
        "categoria": CATEGORIA,
        "tipo_pesquisa": "Pesquisa na Web",
        "termos": TERMOS,
        "url_validacao": url_validacao,
        "observacao": (
            "Valores de 0 a 100 são relativos ao maior ponto "
            "observado entre os cinco termos desta mesma consulta."
        ),
    }

    ARQUIVO_PARAMETROS.write_text(
        json.dumps(parametros, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    resumo = (
        evolucao
        .groupby("termo", as_index=False)
        .agg(
            media_interesse=("interesse_relativo", "mean"),
            maior_interesse=("interesse_relativo", "max"),
            pontos_temporais=("data", "nunique"),
        )
        .sort_values(
            ["media_interesse", "maior_interesse"],
            ascending=False,
        )
    )

    resumo["media_interesse"] = resumo[
        "media_interesse"
    ].round(2)

    print("\nTESTE CONCLUÍDO")
    print(f"Registros temporais: {len(evolucao)}")
    print(f"Registros estaduais: {len(estados)}")

    print("\nResumo:")
    print(resumo.to_string(index=False))

    print(f"\nEvolução: {ARQUIVO_EVOLUCAO}")
    print(f"Estados: {ARQUIVO_ESTADOS}")
    print(f"Parâmetros: {ARQUIVO_PARAMETROS}")

    print("\nURL PARA VALIDAÇÃO OFICIAL:")
    print(url_validacao)

    print(
        "\nIMPORTANTE: não compare estes valores com outra consulta "
        "que use termos ou período diferentes sem uma âncora comum."
    )


if __name__ == "__main__":
    main()
