from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo
import json
import shutil
import time
import argparse

import pandas as pd
from pytrends.request import TrendReq


FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")
ANCORA = "Rock in Rio"
PAIS = "BR"
DIAS_ANALISADOS = 90
TAMANHO_LOTE = 4

# O termo é o texto efetivamente pesquisado no Google Trends.
# A atração oficial é mantida separadamente para ligação com o Power BI.
ENTIDADES = [
    {"artista_id": "marca_heineken", "nome_artista": "HEINEKEN", "termo": "Heineken", "tipo_entidade": "Marca"},
    {"artista_id": "art_foo_fighters", "nome_artista": "FOO FIGHTERS", "termo": "Foo Fighters", "tipo_entidade": "Artista"},
    {"artista_id": "art_rise_against", "nome_artista": "RISE AGAINST", "termo": "Rise Against", "tipo_entidade": "Artista"},
    {"artista_id": "art_the_hives", "nome_artista": "THE HIVES", "termo": "The Hives", "tipo_entidade": "Artista"},
    {"artista_id": "art_nova_twins", "nome_artista": "NOVA TWINS", "termo": "Nova Twins", "tipo_entidade": "Artista"},
    {"artista_id": "art_avenged_sevenfold", "nome_artista": "AVENGED SEVENFOLD", "termo": "Avenged Sevenfold", "tipo_entidade": "Artista"},
    {"artista_id": "art_bring_me_the_horizon", "nome_artista": "BRING ME THE HORIZON", "termo": "Bring Me The Horizon", "tipo_entidade": "Artista"},
    {"artista_id": "art_mgk", "nome_artista": "mgk", "termo": "mgk", "tipo_entidade": "Artista"},
    {"artista_id": "art_sepultura", "nome_artista": "SEPULTURA", "termo": "Sepultura", "tipo_entidade": "Artista"},
    {"artista_id": "art_calvin_harris", "nome_artista": "CALVIN HARRIS", "termo": "Calvin Harris", "tipo_entidade": "Artista"},
    {"artista_id": "art_black_eyed_peas", "nome_artista": "Black Eyed Peas", "termo": "Black Eyed Peas", "tipo_entidade": "Artista"},
    {"artista_id": "art_nelly", "nome_artista": "NELLY", "termo": "Nelly", "tipo_entidade": "Artista"},
    {"artista_id": "art_barao_vermelho_encontro_formacao_original_convida_fernando_magalhaes", "nome_artista": "BARÃO VERMELHO – ENCONTRO FORMAÇÃO ORIGINAL convida Fernando Magalhães", "termo": "Barão Vermelho", "tipo_entidade": "Artista"},
    {"artista_id": "art_elton_john", "nome_artista": "ELTON JOHN", "termo": "Elton John", "tipo_entidade": "Artista"},
    {"artista_id": "art_gilberto_gil", "nome_artista": "GILBERTO GIL", "termo": "Gilberto Gil", "tipo_entidade": "Artista"},
    {"artista_id": "art_jon_batiste", "nome_artista": "JON BATISTE", "termo": "Jon Batiste", "tipo_entidade": "Artista"},
    {"artista_id": "art_luisa_sonza_convida_roberto_menescal", "nome_artista": "LUÍSA SONZA CONVIDA ROBERTO MENESCAL", "termo": "Luísa Sonza", "tipo_entidade": "Artista"},
    {"artista_id": "art_stray_kids", "nome_artista": "STRAY KIDS", "termo": "Stray Kids", "tipo_entidade": "Artista"},
    {"artista_id": "art_alok_keep_art_human", "nome_artista": "ALOK – KEEP ART HUMAN", "termo": "Alok", "tipo_entidade": "Artista"},
    {"artista_id": "art_hwasa", "nome_artista": "HWASA", "termo": "HWASA", "tipo_entidade": "Artista"},
    {"artista_id": "art_nexz", "nome_artista": "NEXZ", "termo": "NEXZ", "tipo_entidade": "Artista"},
    {"artista_id": "art_maroon_5", "nome_artista": "MAROON 5", "termo": "Maroon 5", "tipo_entidade": "Artista"},
    {"artista_id": "art_demi_lovato", "nome_artista": "DEMI LOVATO", "termo": "Demi Lovato", "tipo_entidade": "Artista"},
    {"artista_id": "art_j_balvin", "nome_artista": "J BALVIN", "termo": "J Balvin", "tipo_entidade": "Artista"},
    {"artista_id": "art_pedro_sampaio", "nome_artista": "PEDRO SAMPAIO", "termo": "Pedro Sampaio", "tipo_entidade": "Artista"},
    {"artista_id": "art_twenty_one_pilots", "nome_artista": "TWENTY ONE PILOTS", "termo": "Twenty One Pilots", "tipo_entidade": "Artista"},
    {"artista_id": "art_halsey", "nome_artista": "HALSEY", "termo": "Halsey", "tipo_entidade": "Artista"},
    {"artista_id": "art_lola_young", "nome_artista": "LOLA YOUNG", "termo": "Lola Young", "tipo_entidade": "Artista"},
    {"artista_id": "art_ivete_sangalo", "nome_artista": "IVETE SANGALO", "termo": "Ivete Sangalo", "tipo_entidade": "Artista"},
]

PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_BRUTOS = PASTA_PROJETO / "dados" / "brutos" / "google_trends_rir"
PASTA_TRATADOS = PASTA_PROJETO / "dados" / "tratados"

ARQUIVO_EVOLUCAO = PASTA_TRATADOS / "google_trends_rir_evolucao.csv"
ARQUIVO_ESTADOS = PASTA_TRATADOS / "google_trends_rir_estados.csv"
ARQUIVO_RESUMO = PASTA_TRATADOS / "google_trends_rir_resumo.csv"
ARQUIVO_AUDITORIA = PASTA_TRATADOS / "google_trends_rir_auditoria_lotes.csv"


def criar_cliente():
    return TrendReq(
        hl="pt-BR",
        tz=180,
        timeout=(10, 35),
        retries=0,
        backoff_factor=0,
    )


def dividir_lotes(lista, tamanho):
    return [lista[i:i + tamanho] for i in range(0, len(lista), tamanho)]


def executar_consulta(termos, periodo, tipo, tentativas=6):
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

            if tipo == "evolucao":
                return cliente.interest_over_time()

            return cliente.interest_by_region(
                resolution="REGION",
                inc_low_vol=True,
                inc_geo_code=False,
            )

        except Exception as erro:
            ultimo_erro = erro

            if tentativa == tentativas:
                break

            espera = min(45 * tentativa, 180)
            print(
                f"      Tentativa {tentativa} falhou: {erro}\n"
                f"      Aguardando {espera}s..."
            )
            time.sleep(espera)

    raise RuntimeError(
        f"Consulta {tipo} não concluída: {ultimo_erro}"
    ) from ultimo_erro


def salvar_bruto(dados, nome):
    caminho = PASTA_BRUTOS / nome
    dados.to_csv(caminho, encoding="utf-8-sig")
    return caminho


def carregar_bruto_recente(nome, termos, tipo, data_fim):
    caminho = PASTA_BRUTOS / nome

    if not caminho.exists():
        return None

    modificado_em = datetime.fromtimestamp(
        caminho.stat().st_mtime,
        tz=FUSO_BRASIL,
    ).date()

    if modificado_em != data_fim:
        return None

    try:
        dados = pd.read_csv(
            caminho,
            index_col=0,
            encoding="utf-8-sig",
        )
    except (OSError, ValueError, UnicodeError):
        return None

    if not set(termos).issubset(dados.columns):
        return None

    if tipo == "evolucao":
        try:
            dados.index = pd.to_datetime(dados.index)
        except (TypeError, ValueError):
            return None

        if dados.empty or dados.index.max().date() != data_fim:
            return None

    elif dados.empty:
        return None

    return dados


def evolucao_longa(dados, termos, lote_id):
    resultado = dados.copy().reset_index()

    if "isPartial" in resultado.columns:
        resultado = resultado.drop(columns=["isPartial"])

    resultado = resultado.melt(
        id_vars=["date"],
        value_vars=termos,
        var_name="termo",
        value_name="valor_original_lote",
    )
    resultado = resultado.rename(columns={"date": "data"})
    resultado["data"] = pd.to_datetime(resultado["data"])
    resultado["lote_id"] = lote_id
    return resultado


def estados_longos(dados, termos, lote_id):
    resultado = dados.copy().reset_index()
    coluna_estado = resultado.columns[0]
    resultado = resultado.rename(columns={coluna_estado: "estado"})
    resultado = resultado.melt(
        id_vars=["estado"],
        value_vars=termos,
        var_name="termo",
        value_name="valor_original_lote",
    )
    resultado["lote_id"] = lote_id
    return resultado


def fator_temporal(referencia, grupo):
    base = referencia.merge(
        grupo,
        on="data",
        suffixes=("_referencia", "_grupo"),
    )
    base = base[
        (base["valor_original_lote_referencia"] > 0)
        & (base["valor_original_lote_grupo"] > 0)
    ].copy()

    if base.empty:
        raise ValueError("Não foi possível calcular o fator da âncora temporal.")

    razoes = (
        base["valor_original_lote_referencia"]
        / base["valor_original_lote_grupo"]
    )
    return float(median(razoes.tolist()))


def aplicar_escala_temporal(dados):
    referencia = dados[
        (dados["lote_id"] == 1) & (dados["termo"] == ANCORA)
    ][["data", "valor_original_lote"]]

    partes = []
    fatores = {}

    for lote_id in sorted(dados["lote_id"].unique()):
        grupo = dados[dados["lote_id"] == lote_id].copy()

        if lote_id == 1:
            fator = 1.0
        else:
            ancora_grupo = grupo[grupo["termo"] == ANCORA][
                ["data", "valor_original_lote"]
            ]
            fator = fator_temporal(referencia, ancora_grupo)

        fatores[int(lote_id)] = fator
        grupo["fator_ancora"] = fator
        grupo["valor_escalado"] = grupo["valor_original_lote"] * fator
        partes.append(grupo)

    resultado = pd.concat(partes, ignore_index=True)
    resultado = resultado[resultado["termo"] != ANCORA].copy()

    maximo = resultado["valor_escalado"].max()
    resultado["interesse_comparavel"] = (
        resultado["valor_escalado"] / maximo * 100
    ).round(2)

    return resultado, fatores


def aplicar_escala_estados(dados):
    referencia = dados[
        (dados["lote_id"] == 1) & (dados["termo"] == ANCORA)
    ][["estado", "valor_original_lote"]].rename(
        columns={"valor_original_lote": "ancora_referencia"}
    )

    partes = []

    for lote_id in sorted(dados["lote_id"].unique()):
        grupo = dados[dados["lote_id"] == lote_id].copy()
        ancora = grupo[grupo["termo"] == ANCORA][
            ["estado", "valor_original_lote"]
        ].rename(columns={"valor_original_lote": "ancora_grupo"})

        grupo = grupo.merge(referencia, on="estado", how="left")
        grupo = grupo.merge(ancora, on="estado", how="left")

        grupo["fator_ancora_estado"] = (
            grupo["ancora_referencia"]
            / grupo["ancora_grupo"].replace(0, pd.NA)
        ).fillna(1.0)

        grupo["valor_escalado"] = (
            grupo["valor_original_lote"]
            * grupo["fator_ancora_estado"]
        )
        partes.append(grupo)

    resultado = pd.concat(partes, ignore_index=True)
    resultado = resultado[resultado["termo"] != ANCORA].copy()

    maximos = resultado.groupby("termo")["valor_escalado"].transform("max")
    resultado["indice_estado_termo"] = (
        resultado["valor_escalado"]
        / maximos.replace(0, pd.NA)
        * 100
    ).fillna(0).round(2)

    totais_estado = resultado.groupby("estado")["valor_escalado"].transform("sum")
    resultado["participacao_termos_estado"] = (
        resultado["valor_escalado"]
        / totais_estado.replace(0, pd.NA)
        * 100
    ).fillna(0).round(2)

    return resultado


def adicionar_cadastro(dados):
    cadastro = pd.DataFrame(ENTIDADES)
    return dados.merge(cadastro, on="termo", how="left")


def ler_argumentos():
    parser = argparse.ArgumentParser(description="Coleta histórica do Google Trends.")
    parser.add_argument(
        "--somente-evolucao",
        action="store_true",
        help="Coleta apenas a série histórica de 90 dias; Estados usam o coletor 7d separado.",
    )
    return parser.parse_args()


def main():
    argumentos = ler_argumentos()
    agora = datetime.now(FUSO_BRASIL)
    data_fim = agora.date()
    data_inicio = data_fim - timedelta(days=DIAS_ANALISADOS)
    periodo = f"{data_inicio.isoformat()} {data_fim.isoformat()}"

    PASTA_BRUTOS.mkdir(parents=True, exist_ok=True)
    PASTA_TRATADOS.mkdir(parents=True, exist_ok=True)

    lotes = dividir_lotes(ENTIDADES, TAMANHO_LOTE)
    evolucoes = []
    regioes = []
    auditoria = []

    print("COLETANDO GOOGLE TRENDS — ROCK IN RIO 2026")
    print(f"Período: {periodo}")
    print(f"Entidades monitoradas: {len(ENTIDADES)}")
    print(f"Lotes: {len(lotes)}")
    print("Retomada automática: ativa")

    if ARQUIVO_AUDITORIA.exists():
        sufixo_backup = agora.strftime("%Y-%m-%d_%H-%M-%S")
        arquivo_backup = PASTA_TRATADOS / (
            f"google_trends_rir_auditoria_lotes_anterior_{sufixo_backup}.csv"
        )
        shutil.copy2(ARQUIVO_AUDITORIA, arquivo_backup)
        print(f"Auditoria anterior preservada: {arquivo_backup.name}")

    for numero, lote in enumerate(lotes, start=1):
        termos_lote = [ANCORA] + [item["termo"] for item in lote]
        print(f"\n[{numero}/{len(lotes)}] {', '.join(termos_lote)}")
        inicio_lote = time.perf_counter()
        origem_evolucao = "não iniciado"
        origem_estados = "não iniciado"

        try:
            print("   Evolução temporal...")
            nome_evolucao = f"lote_{numero:02d}_evolucao.csv"
            evolucao = carregar_bruto_recente(
                nome_evolucao,
                termos_lote,
                "evolucao",
                data_fim,
            )

            if evolucao is None:
                evolucao = executar_consulta(
                    termos_lote,
                    periodo,
                    "evolucao",
                )
                salvar_bruto(evolucao, nome_evolucao)
                origem_evolucao = "coletado agora"
            else:
                origem_evolucao = "reutilizado do cache de hoje"
                print("      Reutilizada coleta válida de hoje")

            evolucoes.append(evolucao_longa(evolucao, termos_lote, numero))

            if origem_evolucao == "coletado agora":
                time.sleep(15)

            if argumentos.somente_evolucao:
                origem_estados = "não executado: Estados usam janela exclusiva de 7 dias"
            else:
                print("   Interesse por estado...")
                nome_estados = f"lote_{numero:02d}_estados.csv"
                estados = carregar_bruto_recente(nome_estados, termos_lote, "estados", data_fim)
                if estados is None:
                    estados = executar_consulta(termos_lote, periodo, "estados")
                    salvar_bruto(estados, nome_estados)
                    origem_estados = "coletado agora"
                else:
                    origem_estados = "reutilizado do cache de hoje"
                    print("      Reutilizada coleta válida de hoje")
                regioes.append(estados_longos(estados, termos_lote, numero))

            status = "concluído"
            erro = ""
            print(
                "   Lote concluído "
                f"(evolução: {origem_evolucao}; estados: {origem_estados})"
            )

        except Exception as excecao:
            status = "erro"
            erro = str(excecao)
            print(f"   ERRO NO LOTE: {erro}")

        auditoria.append(
            {
                "coletado_em": agora.isoformat(timespec="seconds"),
                "lote_id": numero,
                "termos": " | ".join(termos_lote),
                "status": status,
                "origem_evolucao": origem_evolucao,
                "origem_estados": origem_estados,
                "duracao_segundos": round(time.perf_counter() - inicio_lote, 2),
                "erro": erro,
            }
        )

        if numero < len(lotes):
            if status == "concluído" and (
                origem_evolucao == "coletado agora"
                or origem_estados == "coletado agora"
            ):
                print("   Pausa de 20 segundos...")
                time.sleep(20)

    auditoria_df = pd.DataFrame(auditoria)
    auditoria_df.to_csv(ARQUIVO_AUDITORIA, index=False, encoding="utf-8-sig")

    erros = auditoria_df[auditoria_df["status"] != "concluído"]

    if not erros.empty:
        raise RuntimeError(
            f"{len(erros)} lote(s) falharam. Consulte: {ARQUIVO_AUDITORIA}"
        )

    evolucao_bruta = pd.concat(evolucoes, ignore_index=True)
    evolucao, fatores = aplicar_escala_temporal(evolucao_bruta)
    evolucao = adicionar_cadastro(evolucao)

    evolucao["pais"] = "Brasil"
    evolucao["geo"] = PAIS
    evolucao["fonte"] = "Google Trends via pytrends"
    evolucao["data_inicio_consulta"] = data_inicio.isoformat()
    evolucao["data_fim_consulta"] = data_fim.isoformat()

    if not argumentos.somente_evolucao:
        estados_brutos = pd.concat(regioes, ignore_index=True)
        estados = aplicar_escala_estados(estados_brutos)
        estados = adicionar_cadastro(estados)
        estados["pais"] = "Brasil"
        estados["geo"] = PAIS
        estados["fonte"] = "Google Trends via pytrends"
        estados["data_inicio_consulta"] = data_inicio.isoformat()
        estados["data_fim_consulta"] = data_fim.isoformat()

    resumo = (
        evolucao
        .groupby(
            ["artista_id", "nome_artista", "termo", "tipo_entidade"],
            as_index=False,
        )
        .agg(
            media_interesse=("interesse_comparavel", "mean"),
            pico_interesse=("interesse_comparavel", "max"),
            data_pico=(
                "data",
                lambda serie: serie.loc[
                    evolucao.loc[serie.index, "interesse_comparavel"].idxmax()
                ],
            ),
            pontos_temporais=("data", "nunique"),
        )
        .sort_values("media_interesse", ascending=False)
        .reset_index(drop=True)
    )
    resumo["media_interesse"] = resumo["media_interesse"].round(2)
    resumo["pico_interesse"] = resumo["pico_interesse"].round(2)
    resumo.insert(0, "ranking_interesse_busca", range(1, len(resumo) + 1))

    evolucao.to_csv(ARQUIVO_EVOLUCAO, index=False, encoding="utf-8-sig")
    if not argumentos.somente_evolucao:
        estados.to_csv(ARQUIVO_ESTADOS, index=False, encoding="utf-8-sig")
    resumo.to_csv(ARQUIVO_RESUMO, index=False, encoding="utf-8-sig")

    parametros = {
        "coletado_em": agora.isoformat(timespec="seconds"),
        "data_inicio": data_inicio.isoformat(),
        "data_fim": data_fim.isoformat(),
        "geo": PAIS,
        "ancora": ANCORA,
        "tamanho_lote": TAMANHO_LOTE,
        "fatores_temporais_por_lote": fatores,
        "entidades": ENTIDADES,
        "nota": (
            "Os lotes foram ligados por uma âncora comum. "
            "interesse_comparavel é um índice reescalado para o conjunto "
            "monitorado e não representa volume absoluto de buscas."
        ),
    }
    (PASTA_BRUTOS / "parametros_coleta.json").write_text(
        json.dumps(parametros, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\nCOLETA DO GOOGLE TRENDS CONCLUÍDA")
    print(f"Registros temporais: {len(evolucao)}")
    print(f"Registros estaduais: {len(estados) if not argumentos.somente_evolucao else 0}")
    print(f"Entidades no resumo: {len(resumo)}")

    print("\nDez maiores médias do índice comparável:")
    print(
        resumo[
            [
                "ranking_interesse_busca",
                "nome_artista",
                "media_interesse",
                "pico_interesse",
                "data_pico",
            ]
        ].head(10).to_string(index=False)
    )

    print(f"\nEvolução: {ARQUIVO_EVOLUCAO}")
    if not argumentos.somente_evolucao:
        print(f"Estados: {ARQUIVO_ESTADOS}")
    print(f"Resumo: {ARQUIVO_RESUMO}")
    print(f"Auditoria: {ARQUIVO_AUDITORIA}")

    print(
        "\nIMPORTANTE: os números são índices relativos de interesse de "
        "busca, não quantidades absolutas de pesquisas."
    )


if __name__ == "__main__":
    main()
