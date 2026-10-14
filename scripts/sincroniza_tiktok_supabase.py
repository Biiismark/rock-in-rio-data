from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

PASTA_PROJETO = Path(__file__).resolve().parents[1]
BASE = PASTA_PROJETO / "dados" / "tratados" / "tiktok"

ARQ_KWORB = BASE / "tiktok_kworb_brasil.csv"
ARQ_POPULAR = BASE / "tiktok_popular_brasil.csv"
ARQ_VIRAL = BASE / "tiktok_viral_brasil.csv"
ARQ_HIST = BASE / "tiktok_historico_sons.csv"
ARQ_RESUMO = BASE / "tiktok_resumo_sons.csv"

CONFLITOS = {
    "tiktok_kworb": "data_ranking,posicao",
    "tiktok_rankings": "data_ranking,tipo_ranking,posicao",
    "tiktok_historico": "url_som,data",
    "tiktok_resumo_sons": "url_som",
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
    if not url:
        raise RuntimeError("SUPABASE_URL não encontrada.")
    if not chave:
        raise RuntimeError("Chave do Supabase não encontrada.")
    return url, chave


def ler(caminho):
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo TikTok ausente: {caminho}")
    try:
        return pd.read_csv(caminho)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def limpar_valor(v):
    if pd.isna(v):
        return None
    if hasattr(v, "item"):
        try:
            v = v.item()
        except Exception:
            pass
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def converter_inteiros(df, colunas):
    for coluna in colunas:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce").round().astype("Int64")
    return df


def preparar_kworb():
    df = ler(ARQ_KWORB)
    mapa = {
        "Data_Ranking": "data_ranking", "Data_Execucao": "data_execucao",
        "Plataforma": "plataforma", "Fonte": "fonte", "Tipo_Ranking": "tipo_ranking",
        "Pais": "pais", "Posicao": "posicao", "Variacao": "variacao",
        "Artista": "artista", "Artista_Normalizado": "artista_normalizado", "Musica": "musica",
    }
    df = df[[c for c in mapa if c in df.columns]].rename(columns=mapa)
    df = converter_inteiros(df, {"posicao"})
    return df.drop_duplicates(["data_ranking", "posicao"], keep="last")


def preparar_rankings():
    frames = [df for df in [ler(ARQ_POPULAR), ler(ARQ_VIRAL)] if not df.empty]
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    mapa = {
        "Data_Ranking": "data_ranking", "Data_Execucao": "data_execucao",
        "Plataforma": "plataforma", "Fonte": "fonte", "Tipo_Ranking": "tipo_ranking",
        "Pais": "pais", "Posicao": "posicao", "Artista": "artista",
        "Artista_Normalizado": "artista_normalizado", "Musica": "musica",
        "Videos_TikTok": "videos_tiktok", "URL_Som": "url_som",
    }
    df = df[[c for c in mapa if c in df.columns]].rename(columns=mapa)
    df = converter_inteiros(df, {"posicao", "videos_tiktok"})
    return df.drop_duplicates(["data_ranking", "tipo_ranking", "posicao"], keep="last")


def preparar_resumo():
    df = ler(ARQ_RESUMO)
    if df.empty:
        return df
    mapa = {
        "URL_Som": "url_som", "Artista": "artista", "Musica": "musica",
        "Videos_TikTok_Atual": "videos_tiktok_atual", "Uso_7D": "uso_7d",
        "Variacao_7D_Pct": "variacao_7d_pct", "Rank_7D_Texto": "rank_7d_texto",
        "Pico_Posicao": "pico_posicao", "Pico_Data": "pico_data",
        "Sequencia_Atual_Dias": "sequencia_atual_dias", "Dias_no_Chart": "dias_no_chart",
        "Primeira_Aparicao": "primeira_aparicao", "Ultima_Aparicao": "ultima_aparicao",
        "Paises": "paises",
    }
    df = df[[c for c in mapa if c in df.columns]].rename(columns=mapa)
    df = converter_inteiros(df, {"videos_tiktok_atual", "uso_7d", "pico_posicao", "sequencia_atual_dias", "dias_no_chart", "paises"})
    return df.drop_duplicates(["url_som"], keep="last")


def preparar_historico(resumo):
    df = ler(ARQ_HIST)
    if df.empty:
        return df
    mapa = {
        "Data": "data", "Artista": "artista", "Musica": "musica", "Rank": "rank",
        "Novos_Videos_TikTok": "novos_videos_tiktok",
        "Videos_TikTok_Acumulados": "videos_tiktok_acumulados", "URL_Som": "url_som",
    }
    df = df[[c for c in mapa if c in df.columns]].rename(columns=mapa)
    df = converter_inteiros(df, {"rank", "novos_videos_tiktok", "videos_tiktok_acumulados"})
    df["origem_historico"] = "coleta_diaria_7d"
    if not resumo.empty:
        extras = [c for c in ["url_som", "primeira_aparicao", "ultima_aparicao", "pico_data", "pico_posicao", "dias_no_chart"] if c in resumo.columns]
        if "url_som" in extras:
            df = df.merge(resumo[extras].drop_duplicates("url_som"), on="url_som", how="left")
    df["data_execucao"] = pd.Timestamp.now(tz="America/Sao_Paulo").strftime("%Y-%m-%d")
    return df.drop_duplicates(["url_som", "data"], keep="last")


def enviar_lotes(cliente, tabela, df, lote=200):
    if df.empty:
        print(f"⚠ {tabela}: sem registros.")
        return
    registros = [{k: limpar_valor(v) for k, v in row.items()} for row in df.to_dict(orient="records")]
    for inicio in range(0, len(registros), lote):
        parte = registros[inicio:inicio + lote]
        cliente.table(tabela).upsert(parte, on_conflict=CONFLITOS[tabela]).execute()
        print(f"  ✓ {tabela}: {min(inicio + lote, len(registros))}/{len(registros)}")


def main():
    print("=" * 72)
    print("SINCRONIZAÇÃO DIÁRIA TIKTOK → SUPABASE")
    print("=" * 72)
    url, chave = carregar_configuracao()
    cliente = create_client(url, chave)
    kworb = preparar_kworb()
    rankings = preparar_rankings()
    resumo = preparar_resumo()
    historico = preparar_historico(resumo)
    print(f"KWORB: {len(kworb)}")
    print(f"Popular + Viral: {len(rankings)}")
    print(f"Histórico 7D disponível nesta execução: {len(historico)}")
    print(f"Resumos de sons: {len(resumo)}")
    enviar_lotes(cliente, "tiktok_kworb", kworb)
    enviar_lotes(cliente, "tiktok_rankings", rankings)
    enviar_lotes(cliente, "tiktok_historico", historico)
    enviar_lotes(cliente, "tiktok_resumo_sons", resumo)
    print("=" * 72)
    print("✓ TIKTOK SINCRONIZADO")
    print("=" * 72)


if __name__ == "__main__":
    main()
