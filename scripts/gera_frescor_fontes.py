# -*- coding: utf-8 -*-
"""Gera uma fotografia simples de frescor e integridade das principais fontes."""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
TRATADOS = RAIZ / "dados" / "tratados"
REFERENCIAS = RAIZ / "dados" / "referencias"
METODOLOGIA = RAIZ / "dados" / "metodologia"
SAIDA = METODOLOGIA / "frescor_fontes.csv"
FUSO = ZoneInfo("America/Sao_Paulo")

FONTES = [
    ("Programação oficial", REFERENCIAS / "programacao.csv", ["data"]),
    ("Charts Brasil", TRATADOS / "presenca_atual_rir_metricas.csv", ["data_referencia", "data"]),
    ("Spotify diário", TRATADOS / "spotify_ranking_diario.csv", ["data", "date", "data_ranking", "data_referencia"]),
    ("TikTok lineup", TRATADOS / "tiktok_rir_artistas.csv", ["data_ranking"]),
    ("Heineken editorial", TRATADOS / "noticias_heineken_rir_publicacoes.csv", ["data", "data_publicacao"]),
    ("Google Trends V2", TRATADOS / "google_trends_v2_evolucao.csv", ["data"]),
]


def descobrir_data(df, candidatas):
    mapa = {str(c).lower(): c for c in df.columns}
    for candidata in candidatas:
        coluna = mapa.get(candidata.lower())
        if not coluna:
            continue
        datas = pd.to_datetime(df[coluna], errors="coerce", utc=True)
        if datas.dropna().empty:
            datas = pd.to_datetime(df[coluna], errors="coerce")
        if not datas.dropna().empty:
            return coluna, datas.min().date().isoformat(), datas.max().date().isoformat()
    return "", "", ""


def main():
    agora = datetime.now(FUSO).isoformat(timespec="seconds")
    registros = []
    for fonte, caminho, datas in FONTES:
        if not caminho.exists():
            registros.append({
                "fonte": fonte, "arquivo": str(caminho.relative_to(RAIZ)).replace("\\", "/"),
                "linhas": 0, "coluna_data": "", "primeira_data": "", "ultima_data": "",
                "status": "ausente", "gerado_em": agora,
            })
            continue
        try:
            df = pd.read_csv(caminho, encoding="utf-8-sig", low_memory=False)
            coluna, primeira, ultima = descobrir_data(df, datas)
            status = "ok" if len(df) > 0 else "vazio"
            registros.append({
                "fonte": fonte, "arquivo": str(caminho.relative_to(RAIZ)).replace("\\", "/"),
                "linhas": int(len(df)), "coluna_data": coluna, "primeira_data": primeira,
                "ultima_data": ultima, "status": status, "gerado_em": agora,
            })
        except Exception as exc:
            registros.append({
                "fonte": fonte, "arquivo": str(caminho.relative_to(RAIZ)).replace("\\", "/"),
                "linhas": 0, "coluna_data": "", "primeira_data": "", "ultima_data": "",
                "status": f"erro:{type(exc).__name__}", "gerado_em": agora,
            })

    METODOLOGIA.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(registros).to_csv(SAIDA, index=False, encoding="utf-8-sig")
    print(pd.DataFrame(registros).to_string(index=False))
    print(f"Frescor salvo em {SAIDA}")


if __name__ == "__main__":
    main()
