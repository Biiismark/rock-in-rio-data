# -*- coding: utf-8 -*-
"""Validação de integridade das bases essenciais do projeto.

Falha somente em problemas estruturais. Resultado nulo de TikTok para o lineup é
válido e não derruba a rotina.
"""
from pathlib import Path

import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
TRATADOS = RAIZ / "dados" / "tratados"
REFERENCIAS = RAIZ / "dados" / "referencias"
METODOLOGIA = RAIZ / "dados" / "metodologia"
SAIDA = METODOLOGIA / "integridade_projeto.csv"


def ler(caminho):
    if not caminho.exists():
        return None
    return pd.read_csv(caminho, encoding="utf-8-sig", dtype=str, low_memory=False).fillna("")


def registrar(registros, teste, ok, detalhe, critico=True):
    registros.append({
        "teste": teste,
        "status": "OK" if ok else "FALHA",
        "critico": bool(critico),
        "detalhe": detalhe,
    })


def main():
    registros = []

    programa = ler(REFERENCIAS / "programacao.csv")
    if programa is None:
        registrar(registros, "programacao_existe", False, "programacao.csv ausente")
    else:
        datas = programa["data"].nunique() if "data" in programa.columns else 0
        artistas = programa["artista_id"].nunique() if "artista_id" in programa.columns else 0
        por_dia = programa.groupby("data").size().to_dict() if "data" in programa.columns else {}
        registrar(registros, "programacao_28_artistas", artistas == 28, f"artistas={artistas}")
        registrar(registros, "programacao_7_dias", datas == 7, f"dias={datas}")
        registrar(registros, "programacao_4_por_dia", bool(por_dia) and all(v == 4 for v in por_dia.values()), f"por_dia={por_dia}")

    presence = ler(TRATADOS / "resumo_presenca_rir_artistas.csv")
    registrar(registros, "presenca_artistas", presence is not None and len(presence) > 0, f"linhas={0 if presence is None else len(presence)}")

    metrics = ler(TRATADOS / "presenca_atual_rir_metricas.csv")
    registrar(registros, "charts_metricas", metrics is not None and len(metrics) > 0, f"linhas={0 if metrics is None else len(metrics)}")

    spotify = ler(TRATADOS / "spotify_ranking_diario.csv")
    registrar(registros, "spotify_diario", spotify is not None and len(spotify) > 0, f"linhas={0 if spotify is None else len(spotify)}")

    tiktok = ler(TRATADOS / "tiktok_rir_artistas.csv")
    if tiktok is None:
        registrar(registros, "tiktok_lineup_camada", False, "arquivo ausente")
    else:
        monitorados = tiktok["artista_id"].nunique() if "artista_id" in tiktok.columns else 0
        encontrados = 0
        if "encontrado" in tiktok.columns:
            encontrados = tiktok[tiktok["encontrado"].astype(str).str.lower().eq("true")]["artista_id"].nunique()
        registrar(registros, "tiktok_lineup_28_monitorados", monitorados == 28, f"monitorados={monitorados}; detectados={encontrados}")

    heineken = ler(TRATADOS / "noticias_heineken_rir_publicacoes.csv")
    registrar(registros, "heineken_dashboard", heineken is not None and len(heineken) > 0, f"linhas={0 if heineken is None else len(heineken)}")

    trends = ler(TRATADOS / "google_trends_v2_evolucao.csv")
    registrar(registros, "trends_v2_evolucao", trends is not None and len(trends) > 0, f"linhas={0 if trends is None else len(trends)}")

    resumo = ler(TRATADOS / "google_trends_v2_resumo.csv")
    entidades = resumo["artista_id"].nunique() if resumo is not None and "artista_id" in resumo.columns else 0
    registrar(registros, "trends_v2_30_entidades", entidades == 30, f"entidades={entidades}")

    saida = pd.DataFrame(registros)
    METODOLOGIA.mkdir(parents=True, exist_ok=True)
    saida.to_csv(SAIDA, index=False, encoding="utf-8-sig")
    print(saida.to_string(index=False))

    falhas = saida[(saida["status"] == "FALHA") & (saida["critico"] == True)]
    if not falhas.empty:
        raise SystemExit("Integridade crítica falhou: " + "; ".join(falhas["teste"].tolist()))

    print("Integridade estrutural: OK")


if __name__ == "__main__":
    main()
