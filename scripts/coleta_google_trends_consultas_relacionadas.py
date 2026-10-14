from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import argparse
import time

import pandas as pd
from pytrends.request import TrendReq

from coleta_google_trends_rir import ENTIDADES


FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")
PAIS = "BR"
TAMANHO_LOTE_SEGURO = 2
TAMANHO_LOTE = 5

PERIODOS = {
    "7d": {"dias": 7, "intervalo_atualizacao": 1},
    "14d": {"dias": 14, "intervalo_atualizacao": 2},
    "30d": {"dias": 30, "intervalo_atualizacao": 3},
    "90d": {"dias": 90, "intervalo_atualizacao": 7},
}

ENTIDADES_CONSULTA = [
    {
        "artista_id": "evento_rock_in_rio",
        "nome_artista": "ROCK IN RIO",
        "termo": "Rock in Rio",
        "tipo_entidade": "Evento",
    },
    *ENTIDADES,
]

PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_BRUTOS = (
    PASTA_PROJETO
    / "dados"
    / "brutos"
    / "google_trends_rir"
    / "consultas_relacionadas"
)
PASTA_TRATADOS = PASTA_PROJETO / "dados" / "tratados"

ARQUIVO_HISTORICO = (
    PASTA_TRATADOS
    / "google_trends_rir_consultas_relacionadas.csv"
)
ARQUIVO_RESUMO = (
    PASTA_TRATADOS
    / "google_trends_rir_consultas_resumo.csv"
)
ARQUIVO_AUDITORIA = (
    PASTA_TRATADOS
    / "google_trends_rir_auditoria_consultas.csv"
)
ARQUIVO_AUDITORIA_GERAL = PASTA_TRATADOS / "google_trends_rir_auditoria.csv"

PASTA_BRUTOS.mkdir(parents=True, exist_ok=True)
PASTA_TRATADOS.mkdir(parents=True, exist_ok=True)


def criar_cliente():
    return TrendReq(
        hl="pt-BR",
        tz=180,
        timeout=(10, 35),
        retries=0,
        backoff_factor=0,
    )


def dividir_lotes(lista, tamanho):
    return [
        lista[indice:indice + tamanho]
        for indice in range(0, len(lista), tamanho)
    ]


def periodo_consulta(data_fim, dias):
    data_inicio = data_fim - timedelta(days=dias - 1)
    return (
        data_inicio,
        f"{data_inicio.isoformat()} {data_fim.isoformat()}",
    )


def historico_existente():
    if not ARQUIVO_HISTORICO.exists():
        return pd.DataFrame()

    return pd.read_csv(
        ARQUIVO_HISTORICO,
        encoding="utf-8-sig",
        dtype=str,
    ).fillna("")


def ultima_coleta_periodo(historico, periodo_id):
    if historico.empty:
        return None

    dados = historico[
        historico["periodo_id"].eq(periodo_id)
    ]

    if dados.empty:
        return None

    datas = pd.to_datetime(
        dados["data_coleta"],
        errors="coerce",
    ).dropna()

    if datas.empty:
        return None

    return datas.max().date()


def periodo_precisa_atualizar(
    historico,
    periodo_id,
    data_coleta,
    intervalo,
):
    ultima = ultima_coleta_periodo(
        historico,
        periodo_id,
    )

    if ultima is None:
        return True, "primeira coleta"

    dias_desde_ultima = (
        data_coleta - ultima
    ).days

    if dias_desde_ultima >= intervalo:
        return True, (
            f"última coleta há {dias_desde_ultima} dia(s)"
        )

    return False, (
        f"cache válido de {ultima.isoformat()}"
    )


def executar_lote(termos, periodo, tentativas=3):
    ultimo_erro = None

    for tentativa in range(1, tentativas + 1):
        try:
            cliente = criar_cliente()
            cliente.build_payload(
                kw_list=termos,
                cat=0,
                timeframe=periodo,
                geo=PAIS,
                gprop="",
            )

            return cliente.related_queries()

        except Exception as erro:
            ultimo_erro = erro

            if "429" in str(erro):
                raise RuntimeError(
                    "BLOQUEIO 429: o Google limitou temporariamente "
                    "as consultas. Aguarde antes de tentar novamente."
                ) from erro

            if tentativa == tentativas:
                break

            espera = min(45 * tentativa, 180)
            print(
                f"      Tentativa {tentativa} falhou: {erro}\n"
                f"      Aguardando {espera}s..."
            )
            time.sleep(espera)

    raise RuntimeError(
        "Consultas relacionadas não concluídas: "
        f"{ultimo_erro}"
    ) from ultimo_erro


def interpretar_valor(valor, tipo_consulta):
    texto = str(valor).strip()
    texto_normalizado = texto.lower()

    if texto_normalizado in {
        "breakout",
        "explodiu",
    }:
        return None, True, "Explodiu"

    numero = pd.to_numeric(
        texto.replace("%", ""),
        errors="coerce",
    )

    if pd.isna(numero):
        return None, False, texto

    numero = float(numero)

    if tipo_consulta == "Em ascensão":
        return numero, False, f"+{numero:.0f}%"

    return numero, False, f"{numero:.0f}"


def transformar_resultado(
    entidade,
    periodo_id,
    dias,
    data_inicio,
    data_fim,
    data_coleta,
    coletado_em,
    resultado_entidade,
):
    registros = []

    tipos = [
        ("top", "Principais"),
        ("rising", "Em ascensão"),
    ]

    for chave, tipo_consulta in tipos:
        tabela = resultado_entidade.get(chave)

        if tabela is None or tabela.empty:
            continue

        tabela = tabela.reset_index(drop=True)

        for indice, linha in tabela.iterrows():
            consulta = str(
                linha.get("query", "")
            ).strip()

            if not consulta:
                continue

            valor_numerico, explodiu, exibicao = (
                interpretar_valor(
                    linha.get("value", ""),
                    tipo_consulta,
                )
            )

            registros.append(
                {
                    "data_coleta": data_coleta.isoformat(),
                    "coletado_em": coletado_em,
                    "artista_id": entidade["artista_id"],
                    "nome_artista": entidade["nome_artista"],
                    "termo_base": entidade["termo"],
                    "tipo_entidade": entidade["tipo_entidade"],
                    "periodo_id": periodo_id,
                    "periodo_dias": dias,
                    "data_inicio_periodo": data_inicio.isoformat(),
                    "data_fim_periodo": data_fim.isoformat(),
                    "tipo_consulta": tipo_consulta,
                    "posicao": indice + 1,
                    "consulta_relacionada": consulta,
                    "valor_google": valor_numerico,
                    "valor_exibicao": exibicao,
                    "explodiu": explodiu,
                    "geo": PAIS,
                    "pais": "Brasil",
                    "fonte": "Google Trends via pytrends",
                }
            )

    return registros


def pasta_snapshot(data_coleta, periodo_id):
    pasta = (
        PASTA_BRUTOS
        / data_coleta.isoformat()
        / periodo_id
    )
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def arquivos_cache_entidade(
    data_coleta,
    periodo_id,
    entidade,
):
    pasta = pasta_snapshot(
        data_coleta,
        periodo_id,
    )
    base = entidade["artista_id"]
    return (
        pasta / f"{base}_principais.csv",
        pasta / f"{base}_ascensao.csv",
    )


def salvar_resultado_bruto(
    data_coleta,
    periodo_id,
    entidade,
    resultado,
):
    arquivo_top, arquivo_rising = (
        arquivos_cache_entidade(
            data_coleta,
            periodo_id,
            entidade,
        )
    )

    top = resultado.get("top")
    rising = resultado.get("rising")

    if top is None:
        top = pd.DataFrame(columns=["query", "value"])

    if rising is None:
        rising = pd.DataFrame(columns=["query", "value"])

    top.to_csv(
        arquivo_top,
        index=False,
        encoding="utf-8-sig",
    )

    rising.to_csv(
        arquivo_rising,
        index=False,
        encoding="utf-8-sig",
    )


def carregar_cache_entidade(
    data_coleta,
    periodo_id,
    entidade,
):
    arquivo_top, arquivo_rising = (
        arquivos_cache_entidade(
            data_coleta,
            periodo_id,
            entidade,
        )
    )

    if not arquivo_top.exists() and not arquivo_rising.exists():
        return None

    resultado = {"top": None, "rising": None}

    if arquivo_top.exists():
        resultado["top"] = pd.read_csv(
            arquivo_top,
            encoding="utf-8-sig",
        )

    if arquivo_rising.exists():
        resultado["rising"] = pd.read_csv(
            arquivo_rising,
            encoding="utf-8-sig",
        )

    return resultado


def remover_snapshot_do_dia(
    historico,
    novos_dados,
):
    if historico.empty or novos_dados.empty:
        return historico

    chaves = novos_dados[
        ["data_coleta", "periodo_id", "artista_id"]
    ].drop_duplicates()
    chaves["remover"] = True

    historico = historico.merge(
        chaves,
        on=["data_coleta", "periodo_id", "artista_id"],
        how="left",
    )

    return historico[
        historico["remover"].isna()
    ].drop(columns=["remover"])


def adicionar_variacao(historico):
    if historico.empty:
        return historico

    resultado = historico.copy()
    resultado["valor_google"] = pd.to_numeric(
        resultado["valor_google"],
        errors="coerce",
    )
    resultado["data_coleta_dt"] = pd.to_datetime(
        resultado["data_coleta"],
        errors="coerce",
    )

    resultado = resultado.sort_values(
        [
            "artista_id",
            "periodo_id",
            "tipo_consulta",
            "consulta_relacionada",
            "data_coleta_dt",
        ]
    )

    grupos = [
        "artista_id",
        "periodo_id",
        "tipo_consulta",
        "consulta_relacionada",
    ]

    resultado["valor_coleta_anterior"] = (
        resultado.groupby(grupos)["valor_google"].shift(1)
    )
    resultado["variacao_vs_coleta_anterior"] = (
        resultado["valor_google"]
        - resultado["valor_coleta_anterior"]
    )

    def verdadeiro(valor):
        return str(valor).strip().lower() in {
            "true",
            "1",
            "sim",
        }

    def seta(linha):
        if verdadeiro(linha.get("explodiu")):
            return "▲"

        variacao = linha.get("variacao_vs_coleta_anterior")

        if pd.isna(variacao):
            return "—"
        if variacao > 0:
            return "▲"
        if variacao < 0:
            return "▼"
        return "—"

    resultado["indicador_movimento"] = resultado.apply(
        seta,
        axis=1,
    )

    return resultado.drop(columns=["data_coleta_dt"])


def gerar_resumo(historico):
    if historico.empty:
        return pd.DataFrame()

    base = historico.copy()
    base["data_coleta_dt"] = pd.to_datetime(
        base["data_coleta"],
        errors="coerce",
    )

    ultima_data = base.groupby(
        ["artista_id", "periodo_id"]
    )["data_coleta_dt"].transform("max")

    atual = base[
        base["data_coleta_dt"].eq(ultima_data)
    ].copy()
    atual["posicao"] = pd.to_numeric(atual["posicao"], errors="coerce").fillna(999999)

    principais = atual[
        atual["tipo_consulta"].eq("Principais")
    ].sort_values("posicao")

    ascensao = atual[
        atual["tipo_consulta"].eq("Em ascensão")
    ].sort_values("posicao")

    linhas = []

    for chaves, grupo in atual.groupby(
        [
            "artista_id",
            "nome_artista",
            "termo_base",
            "tipo_entidade",
            "periodo_id",
            "periodo_dias",
        ]
    ):
        artista_id, nome, termo, tipo, periodo_id, dias = chaves
        top_grupo = principais[
            (principais["artista_id"] == artista_id)
            & (principais["periodo_id"] == periodo_id)
        ]
        rising_grupo = ascensao[
            (ascensao["artista_id"] == artista_id)
            & (ascensao["periodo_id"] == periodo_id)
        ]

        linhas.append(
            {
                "artista_id": artista_id,
                "nome_artista": nome,
                "termo_base": termo,
                "tipo_entidade": tipo,
                "periodo_id": periodo_id,
                "periodo_dias": dias,
                "data_coleta_mais_recente": grupo["data_coleta"].max(),
                "quantidade_principais": len(top_grupo),
                "quantidade_em_ascensao": len(rising_grupo),
                "principal_consulta": (
                    top_grupo.iloc[0]["consulta_relacionada"]
                    if not top_grupo.empty else ""
                ),
                "principal_pontuacao": (
                    top_grupo.iloc[0]["valor_google"]
                    if not top_grupo.empty else ""
                ),
                "maior_consulta_em_ascensao": (
                    rising_grupo.iloc[0]["consulta_relacionada"]
                    if not rising_grupo.empty else ""
                ),
                "maior_crescimento": (
                    rising_grupo.iloc[0]["valor_exibicao"]
                    if not rising_grupo.empty else ""
                ),
            }
        )

    return pd.DataFrame(linhas)


def ler_argumentos():
    parser = argparse.ArgumentParser(
        description=(
            "Coleta controlada de consultas relacionadas "
            "do Google Trends."
        )
    )
    parser.add_argument(
        "--periodo",
        choices=list(PERIODOS),
        default="7d",
        help="Período a processar nesta execução.",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=30,
        help=(
            "Máximo de entidades pendentes nesta execução; elas são "
            "processadas em lotes seguros de duas entidades."
        ),
    )
    parser.add_argument(
        "--artista-id",
        action="append",
        default=[],
        help="Limita a coleta a artista_id(s) específicos; útil para piloto seguro.",
    )
    return parser.parse_args()


def atualizar_auditoria_geral(registros):
    """Acrescenta checkpoint por entidade, sem apagar auditoria de outros módulos."""
    if ARQUIVO_AUDITORIA_GERAL.exists():
        anterior = pd.read_csv(ARQUIVO_AUDITORIA_GERAL, encoding="utf-8-sig", dtype=str)
    else:
        anterior = pd.DataFrame()
    novos = pd.DataFrame(registros)
    if not anterior.empty and not novos.empty:
        chaves = ["data_coleta", "artista_id", "periodo_id", "modulo"]
        marcador = novos[chaves].drop_duplicates().assign(_atual=True)
        anterior = anterior.merge(marcador, on=chaves, how="left")
        anterior = anterior[anterior["_atual"].isna()].drop(columns=["_atual"])
    pd.concat([anterior, novos], ignore_index=True).to_csv(
        ARQUIVO_AUDITORIA_GERAL, index=False, encoding="utf-8-sig"
    )


def main():
    argumentos = ler_argumentos()
    agora = datetime.now(FUSO_BRASIL)
    data_coleta = agora.date()
    coletado_em = agora.isoformat(timespec="seconds")
    historico = historico_existente()
    novos_registros = []
    auditoria = []

    periodo_id = argumentos.periodo
    configuracao = PERIODOS[periodo_id]
    dias = configuracao["dias"]
    data_inicio, periodo = periodo_consulta(
        data_coleta,
        dias,
    )

    print("COLETANDO CONSULTAS RELACIONADAS — GOOGLE TRENDS")
    print(f"Entidades principais: {len(ENTIDADES)}")
    print("Referência adicional: Rock in Rio")
    entidades_consulta = [
        entidade for entidade in ENTIDADES_CONSULTA
        if not argumentos.artista_id or entidade["artista_id"] in argumentos.artista_id
    ]
    print(f"Entidades consultadas: {len(entidades_consulta)}")
    print(f"Período desta execução: {periodo_id}")
    print(f"Limite de novos acessos: {argumentos.limite}")
    print("Cache e retomada automática: ativos")

    resultados = {}
    entidades_cache = []
    entidades_faltantes = []

    for entidade in entidades_consulta:
        cache = carregar_cache_entidade(
            data_coleta,
            periodo_id,
            entidade,
        )
        if cache is None:
            entidades_faltantes.append(entidade)
        else:
            entidades_cache.append(entidade)
            resultados[entidade["termo"]] = cache

    limite = max(0, argumentos.limite)
    entidades_novas = entidades_faltantes[:limite]
    entidades_processadas = entidades_cache + entidades_novas

    print(f"Entidades já no cache: {len(entidades_cache)}")
    print(f"Entidades ainda ausentes: {len(entidades_faltantes)}")
    print(f"Entidades que acessarão o Google agora: {len(entidades_novas)}")

    inicio = time.perf_counter()
    erro = ""
    status = "concluído"

    try:
        if entidades_novas:
            for inicio_lote in range(0, len(entidades_novas), TAMANHO_LOTE_SEGURO):
                lote = entidades_novas[inicio_lote:inicio_lote + TAMANHO_LOTE_SEGURO]
                termos_lote = [entidade["termo"] for entidade in lote]
                print("Consultando lote seguro: " + ", ".join(termos_lote))
                resposta = executar_lote(termos_lote, periodo)
                for entidade in lote:
                    resultado = resposta.get(entidade["termo"], {"top": None, "rising": None})
                    resultados[entidade["termo"]] = resultado
                    salvar_resultado_bruto(data_coleta, periodo_id, entidade, resultado)
                if inicio_lote + TAMANHO_LOTE_SEGURO < len(entidades_novas):
                    print("Pausa de 60 segundos entre lotes de consultas relacionadas...")
                    time.sleep(60)

        for entidade in entidades_processadas:
            resultado = resultados.get(
                entidade["termo"],
                {"top": None, "rising": None},
            )
            novos_registros.extend(
                transformar_resultado(
                    entidade,
                    periodo_id,
                    dias,
                    data_inicio,
                    data_coleta,
                    data_coleta,
                    coletado_em,
                    resultado,
                )
            )

    except Exception as excecao:
        status = "erro"
        erro = str(excecao)
        print(f"ERRO: {erro}")

        # Mesmo em caso de bloqueio, consolida o cache já salvo.
        for entidade in entidades_cache:
            resultado = resultados[entidade["termo"]]
            novos_registros.extend(
                transformar_resultado(
                    entidade,
                    periodo_id,
                    dias,
                    data_inicio,
                    data_coleta,
                    data_coleta,
                    coletado_em,
                    resultado,
                )
            )

    auditoria.append(
        {
            "coletado_em": coletado_em,
            "periodo_id": periodo_id,
            "lote_id": 1,
            "termos": " | ".join(
                entidade["termo"]
                for entidade in entidades_novas
            ),
            "status": status,
            "origem": (
                "cache + coleta controlada"
                if entidades_novas else "somente cache"
            ),
            "registros": len(novos_registros),
            "entidades_cache": len(entidades_cache),
            "entidades_novas": len(entidades_novas),
            "entidades_restantes": max(
                0,
                len(entidades_faltantes) - len(entidades_novas),
            ),
            "duracao_segundos": round(
                time.perf_counter() - inicio,
                2,
            ),
            "erro": erro,
        }
    )

    novos = pd.DataFrame(novos_registros)

    if not novos.empty:
        historico = remover_snapshot_do_dia(
            historico,
            novos,
        )
        historico = pd.concat(
            [historico, novos],
            ignore_index=True,
        )

    historico = adicionar_variacao(historico)

    chaves_unicas = [
        "data_coleta",
        "artista_id",
        "periodo_id",
        "tipo_consulta",
        "consulta_relacionada",
    ]
    historico = (
        historico
        .drop_duplicates(
            subset=chaves_unicas,
            keep="last",
        )
        .sort_values(
            [
                "data_coleta",
                "periodo_dias",
                "nome_artista",
                "tipo_consulta",
                "posicao",
            ]
        )
        .reset_index(drop=True)
    )

    historico.to_csv(
        ARQUIVO_HISTORICO,
        index=False,
        encoding="utf-8-sig",
    )

    resumo = gerar_resumo(historico)
    resumo.to_csv(
        ARQUIVO_RESUMO,
        index=False,
        encoding="utf-8-sig",
    )

    auditoria_df = pd.DataFrame(auditoria)
    auditoria_df.to_csv(
        ARQUIVO_AUDITORIA,
        index=False,
        encoding="utf-8-sig",
    )

    # Estado explícito por entidade: uma resposta vazia é válida e não é zero nem erro.
    checkpoints = []
    for entidade in entidades_processadas + [e for e in entidades_novas if e not in entidades_processadas]:
        resultado = resultados.get(entidade["termo"], {"top": None, "rising": None})
        principais = resultado.get("top")
        ascensao = resultado.get("rising")
        qtd_principais = len(principais) if isinstance(principais, pd.DataFrame) else 0
        qtd_ascensao = len(ascensao) if isinstance(ascensao, pd.DataFrame) else 0
        if status == "erro" and entidade in entidades_novas and entidade["termo"] not in resultados:
            status_entidade = "bloqueado_429" if "429" in erro else "erro_coleta"
        else:
            status_entidade = "ok_com_resultados" if qtd_principais + qtd_ascensao else "ok_sem_resultados"
        checkpoints.append({
            "data_coleta": data_coleta.isoformat(), "coletado_em": coletado_em,
            "artista_id": entidade["artista_id"], "nome_artista": entidade["nome_artista"],
            "tipo_entidade": entidade["tipo_entidade"], "periodo_id": periodo_id,
            "modulo": "consultas_relacionadas", "status": status_entidade,
            "quantidade_resultados": qtd_principais + qtd_ascensao,
            "quantidade_principais": qtd_principais, "quantidade_em_ascensao": qtd_ascensao,
            "erro": erro if status_entidade in {"erro_coleta", "bloqueado_429"} else "",
            "tentativas": 1 if status_entidade.startswith("ok_") else 3,
            "fonte": "Google Trends via pytrends",
        })
    atualizar_auditoria_geral(checkpoints)

    erros = auditoria_df[
        auditoria_df["status"].eq("erro")
    ]

    print("\nCOLETA DE CONSULTAS RELACIONADAS CONCLUÍDA")
    print(f"Novos registros coletados: {len(novos)}")
    print(f"Registros históricos: {len(historico)}")
    print(f"Entidades no resumo: {resumo['artista_id'].nunique() if not resumo.empty else 0}")
    print(f"Períodos disponíveis: {resumo['periodo_id'].nunique() if not resumo.empty else 0}")
    print(f"Lotes com erro: {len(erros)}")
    print(
        "Entidades ainda não coletadas neste período: "
        f"{max(0, len(entidades_faltantes) - len(entidades_novas))}"
    )
    print(f"\nConsultas: {ARQUIVO_HISTORICO}")
    print(f"Resumo: {ARQUIVO_RESUMO}")
    print(f"Auditoria: {ARQUIVO_AUDITORIA}")
    print(
        "\nIMPORTANTE: em 'Principais', 100 representa a consulta "
        "relacionada mais popular. Em 'Em ascensão', o valor representa "
        "crescimento percentual ou a classificação 'Explodiu'."
    )

    if not erros.empty:
        raise RuntimeError(
            "O Google aplicou um bloqueio temporário. "
            "O cache existente foi preservado."
        )


if __name__ == "__main__":
    main()
