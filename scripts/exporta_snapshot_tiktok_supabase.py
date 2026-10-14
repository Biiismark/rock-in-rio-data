from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_SNAPSHOT = PASTA_PROJETO / "dados" / "tratados" / "tiktok" / "supabase_snapshot"
PASTA_METODOLOGIA = PASTA_PROJETO / "dados" / "metodologia"

TABELAS = [
    "tiktok_kworb",
    "tiktok_rankings",
    "tiktok_historico",
    "tiktok_resumo_sons",
    "tiktok_auditoria_historico",
]

COLUNAS_DATA = {
    "tiktok_kworb": "data_ranking",
    "tiktok_rankings": "data_ranking",
    "tiktok_historico": "data",
    "tiktok_resumo_sons": "ultima_aparicao",
    "tiktok_auditoria_historico": "max_data_extraida",
}


def carregar_configuracao():
    load_dotenv(PASTA_PROJETO / ".env")
    url = os.getenv("SUPABASE_URL", "").strip()
    chave = (
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_ANON_KEY", "").strip()
    )
    if not url or not chave:
        raise RuntimeError("Configuração do Supabase ausente.")
    return url, chave


def ler_tabela(cliente, tabela, lote=1000):
    registros = []
    inicio = 0
    while True:
        resposta = cliente.table(tabela).select("*").range(inicio, inicio + lote - 1).execute()
        parte = resposta.data or []
        registros.extend(parte)
        if len(parte) < lote:
            break
        inicio += lote
    return pd.DataFrame(registros)


def resumir(tabela, df):
    coluna_data = COLUNAS_DATA.get(tabela)
    primeira = ""
    ultima = ""
    distintas = 0
    if coluna_data and coluna_data in df.columns and not df.empty:
        datas = pd.to_datetime(df[coluna_data], errors="coerce").dropna()
        if not datas.empty:
            primeira = datas.min().date().isoformat()
            ultima = datas.max().date().isoformat()
            distintas = int(datas.dt.date.nunique())
    return {
        "tabela": tabela,
        "linhas": int(len(df)),
        "colunas": int(len(df.columns)),
        "coluna_data_referencia": coluna_data or "",
        "primeira_data": primeira,
        "ultima_data": ultima,
        "datas_distintas": distintas,
    }


def main():
    PASTA_SNAPSHOT.mkdir(parents=True, exist_ok=True)
    PASTA_METODOLOGIA.mkdir(parents=True, exist_ok=True)

    url, chave = carregar_configuracao()
    cliente = create_client(url, chave)

    auditoria = []
    for tabela in TABELAS:
        df = ler_tabela(cliente, tabela)
        caminho = PASTA_SNAPSHOT / f"{tabela}.csv"
        df.to_csv(caminho, index=False, encoding="utf-8-sig")
        auditoria.append(resumir(tabela, df))
        print(f"{tabela}: {len(df)} linhas -> {caminho}")

    pd.DataFrame(auditoria).to_csv(
        PASTA_METODOLOGIA / "auditoria_tiktok_supabase.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print("Snapshot SQL do TikTok exportado para versionamento no GitHub.")


if __name__ == "__main__":
    main()
