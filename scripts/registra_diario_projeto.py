from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import json
import subprocess

import pandas as pd


FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")

PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_TRATADOS = PASTA_PROJETO / "dados" / "tratados"
PASTA_METODOLOGIA = PASTA_PROJETO / "dados" / "metodologia"
PASTA_LOGS = PASTA_PROJETO / "logs"

ARQUIVO_CONTROLE = PASTA_TRATADOS / "controle_atualizacao_fontes.csv"
ARQUIVO_RESUMO_ARTISTAS = PASTA_TRATADOS / "resumo_presenca_rir_artistas.csv"
ARQUIVO_TRENDS_RESUMO = PASTA_TRATADOS / "google_trends_rir_resumo.csv"
ARQUIVO_TRENDS_AUDITORIA = PASTA_TRATADOS / "google_trends_rir_auditoria_lotes.csv"
ARQUIVO_CHARTS = PASTA_TRATADOS / "charts_brasil_diario.csv"
ARQUIVO_SPOTIFY = PASTA_TRATADOS / "spotify_ranking_diario.csv"

# Camada de imprensa. Os arquivos de publicações/pautas são preferidos porque
# já foram preparados para o dashboard. A base validada mantém a auditoria.
ARQUIVO_NOTICIAS_HISTORICO = PASTA_TRATADOS / "noticias_heineken_rir.csv"
ARQUIVO_NOTICIAS_VALIDADAS = PASTA_TRATADOS / "noticias_heineken_rir_validadas.csv"
ARQUIVO_NOTICIAS_PUBLICACOES = PASTA_TRATADOS / "noticias_heineken_rir_publicacoes.csv"
ARQUIVO_NOTICIAS_PAUTAS = PASTA_TRATADOS / "noticias_heineken_rir_pautas.csv"

ARQUIVO_DIARIO_CSV = PASTA_METODOLOGIA / "diario_projeto.csv"
ARQUIVO_DIARIO_MD = PASTA_METODOLOGIA / "diario_projeto.md"

# Recortes metodológicos aprovados para impedir a mistura com edições antigas.
INICIO_ROCK_IN_RIO_2026 = "2025-09-18"
INICIO_HEINEKEN_ULTIMATE = "2026-05-18"


def ler_csv(caminho):
    if not caminho.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(caminho, encoding="utf-8-sig", low_memory=False)
    except (pd.errors.EmptyDataError, UnicodeDecodeError):
        return pd.DataFrame()


def texto_serie(dados, coluna):
    if dados.empty or coluna not in dados.columns:
        return pd.Series(index=dados.index, dtype=str)
    return dados[coluna].fillna("").astype(str).str.strip()


def mascara_booleanos(dados, coluna):
    return texto_serie(dados, coluna).str.lower().isin({"true", "1", "sim", "yes"})


def contar_booleanos(dados, coluna):
    return int(mascara_booleanos(dados, coluna).sum())


def primeiro_valor(linha, colunas, padrao=""):
    for coluna in colunas:
        if coluna in linha.index:
            valor = linha.get(coluna)
            if pd.notna(valor) and str(valor).strip():
                return valor
    return padrao


def contar_unicos(dados, coluna):
    if dados.empty or coluna not in dados.columns:
        return 0
    valores = texto_serie(dados, coluna)
    return int(valores[valores.ne("")].nunique())


def datas_validas(dados, coluna):
    if dados.empty or coluna not in dados.columns:
        return pd.Series(dtype="datetime64[ns, UTC]")
    return pd.to_datetime(dados[coluna], errors="coerce", utc=True).dropna()


def versao_git():
    try:
        processo = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PASTA_PROJETO,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return processo.stdout.strip() if processo.returncode == 0 else ""


def ultimo_log():
    if not PASTA_LOGS.exists():
        return ""
    arquivos = sorted(
        PASTA_LOGS.glob("atualizacao_rir_*.log"),
        key=lambda caminho: caminho.stat().st_mtime,
        reverse=True,
    )
    return arquivos[0].name if arquivos else ""


def fase_monitoramento(data_registro):
    data = pd.Timestamp(data_registro)
    if data < pd.Timestamp("2026-09-03"):
        return "Pré-festival"
    if data == pd.Timestamp("2026-09-03"):
        return "Véspera do festival"
    if data.date().isoformat() in {
        "2026-09-04", "2026-09-05", "2026-09-06", "2026-09-07",
        "2026-09-11", "2026-09-12", "2026-09-13",
    }:
        return "Dia de festival"
    if data <= pd.Timestamp("2026-09-20"):
        return "Pós-festival — primeiros 7 dias"
    return "Pós-festival"


def metricas_noticias(data_registro):
    historico = ler_csv(ARQUIVO_NOTICIAS_HISTORICO)
    validadas = ler_csv(ARQUIVO_NOTICIAS_VALIDADAS)
    publicacoes = ler_csv(ARQUIVO_NOTICIAS_PUBLICACOES)
    pautas = ler_csv(ARQUIVO_NOTICIAS_PAUTAS)

    # Se a tabela preparada ainda não existir, as confirmadas da auditoria
    # formam a mesma população documental usada pelo dashboard.
    if publicacoes.empty and not validadas.empty:
        confirmadas = texto_serie(validadas, "status_validacao").str.lower().eq("confirmada")
        if "incluir_dashboard" in validadas.columns:
            confirmadas &= mascara_booleanos(validadas, "incluir_dashboard")
        publicacoes = validadas[confirmadas].copy()

    status = texto_serie(validadas, "status_validacao").str.lower()
    acessiveis = texto_serie(validadas, "status_acesso").str.lower().eq("acessível")
    leads = texto_serie(validadas, "lead_noticia").ne("")

    novas_no_dia = 0
    if not historico.empty and "data_coleta" in historico.columns:
        coletas = pd.to_datetime(historico["data_coleta"], errors="coerce")
        novas_no_dia = int((coletas.dt.date.astype(str) == data_registro).sum())

    categorias = texto_serie(publicacoes, "categoria_validada").str.lower()
    relacao = texto_serie(publicacoes, "relacao_rock_in_rio").str.lower()
    assunto = texto_serie(publicacoes, "assunto").str.lower()
    titulos = texto_serie(publicacoes, "titulo").str.lower()

    mascara_rir = (
        categorias.str.contains("rock in rio 2026", regex=False)
        | relacao.str.contains("relação direta", regex=False)
    )
    mascara_ultimate = (
        categorias.str.contains("ultimate", regex=False)
        | assunto.str.contains("ultimate", regex=False)
        | titulos.str.contains("heineken ultimate", regex=False)
    )

    datas_publicacao = datas_validas(publicacoes, "data_publicacao")
    periodo_inicio = datas_publicacao.min().date().isoformat() if not datas_publicacao.empty else ""
    periodo_fim = datas_publicacao.max().date().isoformat() if not datas_publicacao.empty else ""

    pauta_top = ""
    veiculos_pauta_top = 0
    if not pautas.empty:
        coluna_quantidade = next(
            (c for c in ["quantidade_veiculos", "veiculos_distintos", "numero_veiculos"] if c in pautas.columns),
            "",
        )
        if coluna_quantidade:
            ordem = pd.to_numeric(pautas[coluna_quantidade], errors="coerce").fillna(0)
            linha_top = pautas.loc[ordem.idxmax()]
            pauta_top = str(primeiro_valor(
                linha_top,
                ["titulo_pauta", "pauta", "titulo_representativo", "titulo"],
            )).strip()
            quantidade_top = pd.to_numeric(
                linha_top.get(coluna_quantidade),
                errors="coerce",
            )
            veiculos_pauta_top = int(quantidade_top) if pd.notna(quantidade_top) else 0

    # Alternativa segura quando a tabela de pautas ainda não estiver disponível.
    pautas_distintas = len(pautas) if not pautas.empty else 0

    return {
        "noticias_catalogadas_acumuladas": len(historico),
        "noticias_novas_no_dia": novas_no_dia,
        "noticias_processadas_validacao": len(validadas),
        "noticias_confirmadas_dashboard": len(publicacoes),
        "noticias_pendentes_validacao": int(status.eq("pendente").sum()),
        "noticias_irrelevantes": int(status.eq("irrelevante").sum()),
        "paginas_noticias_acessiveis": int(acessiveis.sum()),
        "leads_noticias_recuperados": int(leads.sum()),
        "pautas_noticias_distintas": pautas_distintas,
        "veiculos_noticias_distintos": contar_unicos(publicacoes, "veiculo"),
        "noticias_rock_in_rio_2026": int(mascara_rir.sum()),
        "noticias_heineken_ultimate": int(mascara_ultimate.sum()),
        "periodo_noticias_inicio": periodo_inicio,
        "periodo_noticias_fim": periodo_fim,
        "recorte_rock_in_rio_2026_inicio": INICIO_ROCK_IN_RIO_2026,
        "recorte_heineken_ultimate_inicio": INICIO_HEINEKEN_ULTIMATE,
        "pauta_maior_repercussao": pauta_top,
        "veiculos_pauta_maior_repercussao": veiculos_pauta_top,
    }


def criar_registro():
    agora = datetime.now(FUSO_BRASIL)
    data_registro = agora.date().isoformat()
    controle = ler_csv(ARQUIVO_CONTROLE)
    artistas = ler_csv(ARQUIVO_RESUMO_ARTISTAS)
    trends = ler_csv(ARQUIVO_TRENDS_RESUMO)
    auditoria_trends = ler_csv(ARQUIVO_TRENDS_AUDITORIA)
    charts = ler_csv(ARQUIVO_CHARTS)
    spotify = ler_csv(ARQUIVO_SPOTIFY)

    fontes_disponiveis = 0
    fontes_ausentes = 0
    ultima_data_geral = ""
    datas_fontes = {}

    if not controle.empty:
        status = texto_serie(controle, "status_arquivo")
        fontes_disponiveis = int((status == "disponível").sum())
        fontes_ausentes = int((status != "disponível").sum())
        if "ultima_data" in controle.columns:
            datas = pd.to_datetime(controle["ultima_data"], errors="coerce").dropna()
            if not datas.empty:
                ultima_data_geral = datas.max().date().isoformat()
            for _, linha in controle.iterrows():
                datas_fontes[str(linha.get("nome_tabela", ""))] = str(linha.get("ultima_data", ""))

    artistas_com_presenca = contar_booleanos(artistas, "tem_presenca_atual")
    artistas_sem_presenca = max(len(artistas) - artistas_com_presenca, 0)

    lider_trends = ""
    media_lider_trends = ""
    if not trends.empty:
        coluna_ordem = "ranking_interesse_busca" if "ranking_interesse_busca" in trends.columns else "media_interesse"
        ascendente = coluna_ordem == "ranking_interesse_busca"
        lider = trends.sort_values(coluna_ordem, ascending=ascendente).iloc[0]
        lider_trends = str(lider.get("nome_artista", ""))
        media_lider_trends = lider.get("media_interesse", "")

    lotes_concluidos = 0
    lotes_com_erro = 0
    if not auditoria_trends.empty and "status" in auditoria_trends.columns:
        status_trends = texto_serie(auditoria_trends, "status")
        lotes_concluidos = int((status_trends == "concluído").sum())
        lotes_com_erro = int((status_trends != "concluído").sum())

    registro = {
        "data_registro": data_registro,
        "registrado_em": agora.isoformat(timespec="seconds"),
        "fase_monitoramento": fase_monitoramento(data_registro),
        "ultima_data_geral": ultima_data_geral,
        "fontes_disponiveis": fontes_disponiveis,
        "fontes_ausentes": fontes_ausentes,
        "datas_por_fonte_json": json.dumps(datas_fontes, ensure_ascii=False, sort_keys=True),
        "registros_spotify_acumulados": len(spotify),
        "registros_charts_acumulados": len(charts),
        "artistas_analisados": len(artistas),
        "artistas_com_presenca_atual": artistas_com_presenca,
        "artistas_sem_presenca_atual": artistas_sem_presenca,
        "entidades_google_trends": len(trends),
        "lider_interesse_busca": lider_trends,
        "media_lider_interesse_busca": media_lider_trends,
        "lotes_trends_concluidos": lotes_concluidos,
        "lotes_trends_com_erro": lotes_com_erro,
        "commit_git": versao_git(),
        "ultimo_log_atualizador": ultimo_log(),
        "observacoes_manuais": "",
    }
    registro.update(metricas_noticias(data_registro))
    return registro


def salvar_csv(registro):
    novo = pd.DataFrame([registro])
    if ARQUIVO_DIARIO_CSV.exists():
        anterior = pd.read_csv(ARQUIVO_DIARIO_CSV, encoding="utf-8-sig", dtype={"data_registro": str})
        diario = pd.concat([anterior, novo], ignore_index=True)
    else:
        diario = novo

    # Uma fotografia factual por dia. Reexecuções preservam a última observação manual.
    if "observacoes_manuais" in diario.columns:
        diario["observacoes_manuais"] = diario["observacoes_manuais"].fillna("").astype(str).str.strip()
        diario["observacoes_manuais"] = diario.groupby("data_registro")["observacoes_manuais"].transform(
            lambda serie: next((v for v in reversed(serie.tolist()) if v), "")
        )

    diario = diario.drop_duplicates(subset=["data_registro"], keep="last").sort_values("data_registro").reset_index(drop=True)
    diario.to_csv(ARQUIVO_DIARIO_CSV, index=False, encoding="utf-8-sig")
    return diario


def valor_inteiro(linha, coluna):
    valor = pd.to_numeric(linha.get(coluna, 0), errors="coerce")
    return int(valor) if pd.notna(valor) else 0


def texto_valido(linha, coluna):
    valor = linha.get(coluna, "")
    if pd.isna(valor):
        return ""
    return str(valor).strip()


def gerar_markdown(diario):
    linhas = [
        "# Diário metodológico — Rock in Rio 2026",
        "",
        "Registro factual gerado automaticamente pelas bases do projeto. As interpretações analíticas devem ser redigidas separadamente.",
        "",
    ]

    for _, registro in diario.sort_values("data_registro", ascending=False).iterrows():
        linhas.extend([
            f"## {registro['data_registro']}",
            "",
            f"- Fase do monitoramento: {texto_valido(registro, 'fase_monitoramento')}",
            f"- Registro atualizado em: {texto_valido(registro, 'registrado_em')}",
            f"- Última data disponível nas bases: {texto_valido(registro, 'ultima_data_geral')}",
            f"- Fontes disponíveis/ausentes: {valor_inteiro(registro, 'fontes_disponiveis')}/{valor_inteiro(registro, 'fontes_ausentes')}",
            f"- Spotify acumulado: {valor_inteiro(registro, 'registros_spotify_acumulados'):,} registros",
            f"- Charts acumulados: {valor_inteiro(registro, 'registros_charts_acumulados'):,} registros",
            f"- Artistas com presença atual: {valor_inteiro(registro, 'artistas_com_presenca_atual')} de {valor_inteiro(registro, 'artistas_analisados')}",
            f"- Maior média de interesse relativo no Trends: {texto_valido(registro, 'lider_interesse_busca')} ({texto_valido(registro, 'media_lider_interesse_busca')})",
            f"- Lotes do Google Trends concluídos/com erro: {valor_inteiro(registro, 'lotes_trends_concluidos')}/{valor_inteiro(registro, 'lotes_trends_com_erro')}",
        ])

        noticias_registradas = pd.notna(
            registro.get("noticias_catalogadas_acumuladas", pd.NA)
        )
        if noticias_registradas:
            linhas.extend([
                "",
                "### Monitoramento de imprensa",
                "",
                f"- Publicações catalogadas: {valor_inteiro(registro, 'noticias_catalogadas_acumuladas'):,}",
                f"- Novas publicações catalogadas no dia: {valor_inteiro(registro, 'noticias_novas_no_dia'):,}",
                f"- Publicações confirmadas para o dashboard: {valor_inteiro(registro, 'noticias_confirmadas_dashboard'):,}",
                f"- Pautas distintas: {valor_inteiro(registro, 'pautas_noticias_distintas'):,}",
                f"- Veículos distintos: {valor_inteiro(registro, 'veiculos_noticias_distintos'):,}",
                f"- Rock in Rio 2026 / Heineken Ultimate: {valor_inteiro(registro, 'noticias_rock_in_rio_2026')}/{valor_inteiro(registro, 'noticias_heineken_ultimate')}",
                f"- Leads recuperados / páginas acessíveis: {valor_inteiro(registro, 'leads_noticias_recuperados')}/{valor_inteiro(registro, 'paginas_noticias_acessiveis')}",
                f"- Pendentes / irrelevantes: {valor_inteiro(registro, 'noticias_pendentes_validacao')}/{valor_inteiro(registro, 'noticias_irrelevantes')}",
                f"- Período das publicações confirmadas: {texto_valido(registro, 'periodo_noticias_inicio')} a {texto_valido(registro, 'periodo_noticias_fim')}",
            ])

            pauta = texto_valido(registro, "pauta_maior_repercussao")
            if pauta:
                linhas.append(
                    f"- Pauta com maior repercussão: {pauta} ({valor_inteiro(registro, 'veiculos_pauta_maior_repercussao')} veículos)"
                )
        else:
            linhas.extend([
                "",
                "- Monitoramento de imprensa: ainda não integrado nesta fotografia histórica.",
            ])

        observacao = texto_valido(registro, "observacoes_manuais")
        if observacao:
            linhas.append(f"- Observações: {observacao}")
        linhas.append("")

    ARQUIVO_DIARIO_MD.write_text("\n".join(linhas), encoding="utf-8")


def main():
    PASTA_METODOLOGIA.mkdir(parents=True, exist_ok=True)
    print("REGISTRANDO DIÁRIO METODOLÓGICO DO PROJETO")
    registro = criar_registro()
    diario = salvar_csv(registro)
    gerar_markdown(diario)

    print("\nDIÁRIO ATUALIZADO")
    print(f"Data registrada: {registro['data_registro']}")
    print(f"Fase do monitoramento: {registro['fase_monitoramento']}")
    print(f"Entradas acumuladas: {len(diario)}")
    print(f"Artistas com presença atual: {registro['artistas_com_presenca_atual']}/{registro['artistas_analisados']}")
    print(f"Google Trends: {registro['lotes_trends_concluidos']} lote(s) concluído(s), {registro['lotes_trends_com_erro']} com erro")
    print("Monitoramento de imprensa:")
    print(f" - {registro['noticias_catalogadas_acumuladas']} publicação(ões) catalogada(s)")
    print(f" - {registro['noticias_novas_no_dia']} nova(s) na data da execução")
    print(f" - {registro['noticias_confirmadas_dashboard']} confirmada(s) para o dashboard")
    print(f" - {registro['pautas_noticias_distintas']} pauta(s) distinta(s)")
    print(f" - {registro['veiculos_noticias_distintos']} veículo(s) distinto(s)")
    print(f"\nCSV factual: {ARQUIVO_DIARIO_CSV}")
    print(f"Diário legível: {ARQUIVO_DIARIO_MD}")


if __name__ == "__main__":
    main()
