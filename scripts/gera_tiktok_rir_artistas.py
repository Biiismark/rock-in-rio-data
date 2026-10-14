# -*- coding: utf-8 -*-
"""Gera a camada TikTok específica dos 28 artistas do Palco Mundo.

O arquivo de saída não transforma ausência em zero de uso no TikTok. Para cada
fonte e artista, registra se houve ou não correspondência na fotografia mais
recente disponível daquela fonte. O site deve exibir somente linhas com
`encontrado=True` e, quando não houver nenhuma, informar que nenhum artista do
line-up foi detectado nas listas monitoradas.
"""
from pathlib import Path
import re
import unicodedata

import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
TRATADOS = RAIZ / "dados" / "tratados"
REFERENCIAS = RAIZ / "dados" / "referencias"
SNAPSHOT = TRATADOS / "tiktok" / "supabase_snapshot"
SAIDA = TRATADOS / "tiktok_rir_artistas.csv"

FONTES = [
    ("KWORB TikTok Brasil", SNAPSHOT / "tiktok_kworb.csv"),
    ("TrendingTikTokSongs", SNAPSHOT / "tiktok_rankings.csv"),
]

ALIASES_EXTRAS = {
    "art_mgk": ["machine gun kelly", "mgk"],
    "art_barao_vermelho_encontro_formacao_original_convida_fernando_magalhaes": ["barao vermelho"],
    "art_luisa_sonza_convida_roberto_menescal": ["luisa sonza"],
    "art_alok_keep_art_human": ["alok"],
    "art_j_balvin": ["j balvin", "jbalvin"],
    "art_black_eyed_peas": ["black eyed peas", "the black eyed peas"],
    "art_twenty_one_pilots": ["twenty one pilots", "21 pilots"],
}


def normalizar(valor):
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.lower().replace("&", " e ")
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def aliases_programacao(linha):
    nome = str(linha.get("nome_artista", ""))
    base = re.split(r"\s+CONVIDA\s+|\s+[–—-]\s+", nome, maxsplit=1, flags=re.IGNORECASE)[0]
    aliases = {normalizar(nome), normalizar(base)}
    aliases.update(normalizar(a) for a in ALIASES_EXTRAS.get(str(linha.get("artista_id", "")), []))
    return sorted(a for a in aliases if len(a) >= 3)


def corresponde(artista_fonte, aliases):
    origem = normalizar(artista_fonte)
    for alias in aliases:
        if origem == alias or re.search(rf"(^|\s){re.escape(alias)}($|\s)", origem):
            return alias
    return ""


def ultima_data(df):
    if "data_ranking" not in df.columns or df.empty:
        return ""
    datas = pd.to_datetime(df["data_ranking"], errors="coerce")
    if datas.dropna().empty:
        return ""
    return datas.max().date().isoformat()


def main():
    programa = pd.read_csv(REFERENCIAS / "programacao.csv", encoding="utf-8-sig", dtype=str).fillna("")
    programa = programa.drop_duplicates(subset=["artista_id"]).copy()

    registros = []
    for nome_fonte, caminho in FONTES:
        if not caminho.exists():
            print(f"{nome_fonte}: snapshot ausente — {caminho}")
            continue

        df = pd.read_csv(caminho, encoding="utf-8-sig", dtype=str).fillna("")
        data_ref = ultima_data(df)
        if not data_ref:
            print(f"{nome_fonte}: sem data válida")
            continue

        fotografia = df[pd.to_datetime(df["data_ranking"], errors="coerce").dt.date.astype(str) == data_ref].copy()
        print(f"{nome_fonte}: {len(fotografia)} registros em {data_ref}")

        for _, artista in programa.iterrows():
            aliases = aliases_programacao(artista)
            matches = []
            for idx, linha in fotografia.iterrows():
                alias = corresponde(linha.get("artista", ""), aliases)
                if alias:
                    matches.append((idx, linha, alias))

            if matches:
                for _, linha, alias in matches:
                    registros.append({
                        "data_ranking": data_ref,
                        "fonte": nome_fonte,
                        "tipo_ranking": linha.get("tipo_ranking", "Trending"),
                        "artista_id": artista["artista_id"],
                        "nome_artista": artista["nome_artista"],
                        "encontrado": True,
                        "ocorrencias_artista_fonte": len(matches),
                        "posicao": linha.get("posicao", ""),
                        "musica": linha.get("musica", ""),
                        "artista_fonte": linha.get("artista", ""),
                        "criterio_match": f"alias:{alias}",
                    })
            else:
                registros.append({
                    "data_ranking": data_ref,
                    "fonte": nome_fonte,
                    "tipo_ranking": "",
                    "artista_id": artista["artista_id"],
                    "nome_artista": artista["nome_artista"],
                    "encontrado": False,
                    "ocorrencias_artista_fonte": 0,
                    "posicao": "",
                    "musica": "",
                    "artista_fonte": "",
                    "criterio_match": "nao_detectado_na_lista_monitorada",
                })

    colunas = [
        "data_ranking", "fonte", "tipo_ranking", "artista_id", "nome_artista",
        "encontrado", "ocorrencias_artista_fonte", "posicao", "musica",
        "artista_fonte", "criterio_match",
    ]
    saida = pd.DataFrame(registros, columns=colunas)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    saida.to_csv(SAIDA, index=False, encoding="utf-8-sig")

    encontrados = saida[saida["encontrado"].astype(str).str.lower().eq("true")] if not saida.empty else saida
    print(f"Saída: {SAIDA}")
    print(f"Artistas do lineup detectados: {encontrados['artista_id'].nunique() if not encontrados.empty else 0}")
    print(f"Ocorrências detectadas: {len(encontrados)}")


if __name__ == "__main__":
    main()
