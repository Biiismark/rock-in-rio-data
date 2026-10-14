"""Coleta segura de interesse por estado no Google Trends (Brasil, 7 dias).

Executa uma entidade por vez, mantém cache/checkpoint diário e nunca substitui
dados válidos por erro ou bloqueio. Os índices são relativos à própria entidade
na janela de sete dias, não representam volume absoluto de buscas.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import json
import time
import argparse

import pandas as pd
from pytrends.request import TrendReq

from coleta_google_trends_rir import ENTIDADES, ANCORA, PAIS

FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")
PERIODO_ID = "7d"
PERIODO_DIAS = 7
PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_BRUTOS = PASTA_PROJETO / "dados" / "brutos" / "google_trends_rir" / "estados_7d"
PASTA_TRATADOS = PASTA_PROJETO / "dados" / "tratados"
ARQUIVO_ESTADOS = PASTA_TRATADOS / "google_trends_rir_estados_7d.csv"
ARQUIVO_AUDITORIA = PASTA_TRATADOS / "google_trends_rir_auditoria.csv"

ENTIDADES_ESTADOS = [
    {"artista_id": "evento_rock_in_rio", "nome_artista": "ROCK IN RIO", "termo": ANCORA, "tipo_entidade": "Evento"},
] + ENTIDADES


def agora_brasil():
    return datetime.now(FUSO_BRASIL)


def periodo_7d(data_fim: date):
    inicio = data_fim - timedelta(days=PERIODO_DIAS - 1)
    return inicio, f"{inicio.isoformat()} {data_fim.isoformat()}"


def e_429(erro: Exception) -> bool:
    texto = str(erro).lower()
    return "429" in texto or "too many requests" in texto or "rate limit" in texto


def ler_csv(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(caminho, encoding="utf-8-sig", dtype=str)
    except (OSError, ValueError, UnicodeError):
        return pd.DataFrame()


def salvar_csv(df: pd.DataFrame, caminho: Path):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    df.to_csv(temporario, index=False, encoding="utf-8-sig")
    temporario.replace(caminho)


def ja_finalizado(auditoria: pd.DataFrame, entidade_id: str, data_coleta: str) -> bool:
    if auditoria.empty:
        return False
    atual = auditoria[
        (auditoria.get("modulo", pd.Series(dtype=str)) == "estados")
        & (auditoria.get("artista_id", pd.Series(dtype=str)) == entidade_id)
        & (auditoria.get("data_coleta", pd.Series(dtype=str)) == data_coleta)
    ]
    return not atual.empty and atual.iloc[-1].get("status") in {"ok_com_resultados", "ok_sem_resultados"}


def registrar_auditoria(auditoria: pd.DataFrame, registro: dict) -> pd.DataFrame:
    chaves = (auditoria.get("modulo", pd.Series(dtype=str)).eq(registro["modulo"])) & (auditoria.get("artista_id", pd.Series(dtype=str)).eq(registro["artista_id"])) & (auditoria.get("data_coleta", pd.Series(dtype=str)).eq(registro["data_coleta"]))
    auditoria = auditoria.loc[~chaves].copy() if not auditoria.empty else auditoria
    return pd.concat([auditoria, pd.DataFrame([registro])], ignore_index=True)


def consultar(termo: str, periodo: str, tentativas: int = 3):
    ultimo = None
    for tentativa in range(1, tentativas + 1):
        try:
            cliente = TrendReq(hl="pt-BR", tz=180, timeout=(10, 35), retries=0, backoff_factor=0)
            cliente.build_payload(kw_list=[termo], cat=0, timeframe=periodo, geo=PAIS, gprop="")
            return cliente.interest_by_region(resolution="REGION", inc_low_vol=True, inc_geo_code=False), tentativa
        except Exception as erro:
            ultimo = erro
            if e_429(erro):
                raise
            if tentativa < tentativas:
                time.sleep(min(20 * tentativa, 90))
    raise RuntimeError(str(ultimo))


def linhas_estados(dados: pd.DataFrame, entidade: dict, agora: datetime, inicio: date, fim: date):
    if dados is None or dados.empty or entidade["termo"] not in dados.columns:
        return []
    base = dados.reset_index().rename(columns={dados.index.name or "index": "estado", entidade["termo"]: "valor_google"})
    base["valor_google"] = pd.to_numeric(base["valor_google"], errors="coerce").fillna(0)
    base = base[base["valor_google"] > 0].copy()
    if base.empty:
        return []
    base["indice_estado_termo"] = (base["valor_google"] / base["valor_google"].max() * 100).round(2)
    return [
        {
            "data_coleta": fim.isoformat(), "coletado_em": agora.isoformat(timespec="seconds"),
            "artista_id": entidade["artista_id"], "nome_artista": entidade["nome_artista"],
            "termo_base": entidade["termo"], "tipo_entidade": entidade["tipo_entidade"],
            "periodo_id": PERIODO_ID, "periodo_dias": PERIODO_DIAS,
            "data_inicio_periodo": inicio.isoformat(), "data_fim_periodo": fim.isoformat(),
            "estado": linha.estado, "valor_google": linha.valor_google,
            "indice_estado_termo": linha.indice_estado_termo, "geo": PAIS, "pais": "Brasil",
            "fonte": "Google Trends via pytrends", "status_coleta": "ok_com_resultados",
        }
        for linha in base.itertuples(index=False)
    ]


def main():
    parser = argparse.ArgumentParser(description="Coleta segura de Estados no Google Trends.")
    parser.add_argument("--artista-id", action="append", default=[], help="Limita a coleta a um artista_id; pode repetir.")
    parser.add_argument("--registrar-pendentes", action="store_true", help="Registra pendências na auditoria sem acessar o Google.")
    parser.add_argument("--marcar-bloqueado", help="Registra bloqueio 429 já detectado, sem nova consulta.")
    argumentos = parser.parse_args()
    agora = agora_brasil(); fim = agora.date(); inicio, periodo = periodo_7d(fim)
    PASTA_BRUTOS.mkdir(parents=True, exist_ok=True); PASTA_TRATADOS.mkdir(parents=True, exist_ok=True)
    estados = ler_csv(ARQUIVO_ESTADOS); auditoria = ler_csv(ARQUIVO_AUDITORIA)
    entidades = [e for e in ENTIDADES_ESTADOS if not argumentos.artista_id or e["artista_id"] in argumentos.artista_id]
    if argumentos.marcar_bloqueado:
        entidade = next(e for e in ENTIDADES_ESTADOS if e["artista_id"] == argumentos.marcar_bloqueado)
        auditoria = registrar_auditoria(auditoria, {"data_coleta": fim.isoformat(), "coletado_em": agora.isoformat(timespec="seconds"), **{k: entidade[k] for k in ("artista_id", "nome_artista", "tipo_entidade")}, "periodo_id": PERIODO_ID, "modulo": "estados", "status": "bloqueado_429", "quantidade_resultados": 0, "quantidade_principais": 0, "quantidade_em_ascensao": 0, "erro": "HTTP 429 detectado; coleta interrompida com segurança.", "tentativas": 1, "fonte": "Google Trends via pytrends"})
        salvar_csv(auditoria, ARQUIVO_AUDITORIA)
        return
    if argumentos.registrar_pendentes:
        for entidade in entidades:
            if ja_finalizado(auditoria, entidade["artista_id"], fim.isoformat()):
                continue
            atual = auditoria[(auditoria["modulo"] == "estados") & (auditoria["artista_id"] == entidade["artista_id"]) & (auditoria["data_coleta"] == fim.isoformat())]
            if not atual.empty and atual.iloc[-1]["status"] in {"bloqueado_429", "erro_coleta"}:
                continue
            auditoria = registrar_auditoria(auditoria, {"data_coleta": fim.isoformat(), "coletado_em": agora.isoformat(timespec="seconds"), **{k: entidade[k] for k in ("artista_id", "nome_artista", "tipo_entidade")}, "periodo_id": PERIODO_ID, "modulo": "estados", "status": "nao_coletado", "quantidade_resultados": 0, "quantidade_principais": 0, "quantidade_em_ascensao": 0, "erro": "Pendente após bloqueio 429 em outra entidade; nenhuma nova consulta foi feita.", "tentativas": 0, "fonte": "Google Trends via pytrends"})
        salvar_csv(auditoria, ARQUIVO_AUDITORIA)
        return
    for indice, entidade in enumerate(entidades, start=1):
        if ja_finalizado(auditoria, entidade["artista_id"], fim.isoformat()):
            print(f"[{indice}/{len(entidades)}] cache diário: {entidade['nome_artista']}")
            continue
        tentativas = 0; erro = ""; status = "erro_coleta"; linhas = []
        try:
            dados, tentativas = consultar(entidade["termo"], periodo)
            (PASTA_BRUTOS / f"{fim.isoformat()}_{entidade['artista_id']}.csv").write_text(dados.to_csv(encoding="utf-8-sig"), encoding="utf-8-sig")
            linhas = linhas_estados(dados, entidade, agora, inicio, fim)
            status = "ok_com_resultados" if linhas else "ok_sem_resultados"
        except Exception as excecao:
            erro = str(excecao); status = "bloqueado_429" if e_429(excecao) else "erro_coleta"
        registro = {"data_coleta": fim.isoformat(), "coletado_em": agora.isoformat(timespec="seconds"), **{k: entidade[k] for k in ("artista_id", "nome_artista", "tipo_entidade")}, "periodo_id": PERIODO_ID, "modulo": "estados", "status": status, "quantidade_resultados": len(linhas), "quantidade_principais": 0, "quantidade_em_ascensao": 0, "erro": erro, "tentativas": tentativas, "fonte": "Google Trends via pytrends"}
        auditoria = registrar_auditoria(auditoria, registro); salvar_csv(auditoria, ARQUIVO_AUDITORIA)
        if linhas:
            chave = (estados.get("data_coleta", pd.Series(dtype=str)).eq(fim.isoformat())) & (estados.get("artista_id", pd.Series(dtype=str)).eq(entidade["artista_id"]))
            estados = estados.loc[~chave].copy() if not estados.empty else estados
            estados = pd.concat([estados, pd.DataFrame(linhas)], ignore_index=True); salvar_csv(estados, ARQUIVO_ESTADOS)
        print(f"[{indice}/{len(entidades)}] {entidade['nome_artista']}: {status}")
        if status == "bloqueado_429":
            print("Google limitou as consultas; parada segura. Execute novamente mais tarde para retomar.")
            return
        if indice < len(entidades):
            time.sleep(20 if indice % 2 == 0 else 5)


if __name__ == "__main__":
    main()
