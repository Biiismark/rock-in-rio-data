import os
import re
import json
import time
import unicodedata
from io import StringIO
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

KWORB_URL = "https://kworb.net/charts/tiktok/br.html"
POPULAR_URL = "https://trendingtiktoksongs.com/pt-br/charts/br"
VIRAL_URL = "https://trendingtiktoksongs.com/pt-br/charts/br/viral"
BASE_TTS = "https://trendingtiktoksongs.com"

PASTA_BRUTOS = os.path.join("dados", "brutos", "tiktok")
PASTA_TRATADOS = os.path.join("dados", "tratados", "tiktok")
DATA_EXECUCAO = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

session = requests.Session()
session.headers.update(HEADERS)


def criar_pastas():
    os.makedirs(PASTA_BRUTOS, exist_ok=True)
    os.makedirs(PASTA_TRATADOS, exist_ok=True)


def corrigir_mojibake(texto):
    if texto is None:
        return ""
    texto = str(texto)
    if any(x in texto for x in ("Ã", "Â", "â€", "â€™", "â€œ", "â€", "â")):
        try:
            corrigido = texto.encode("latin1").decode("utf-8")
            if corrigido:
                return corrigido
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return texto


def normalizar(texto):
    texto = corrigir_mojibake(texto)
    texto = unicodedata.normalize("NFKD", texto.lower().strip())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def baixar(url, nome_html=None):
    print(f"\nAcessando: {url}")
    r = session.get(url, timeout=35)
    print("Status:", r.status_code)
    r.raise_for_status()
    if not r.encoding or r.encoding.lower() in ("iso-8859-1", "latin-1"):
        r.encoding = "utf-8"
    html = r.text
    if nome_html:
        caminho = os.path.join(PASTA_BRUTOS, nome_html)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(html)
    return html


def videos_para_int(valor):
    if valor is None:
        return None
    s = corrigir_mojibake(str(valor)).lower().replace("\xa0", " ").strip()
    s = s.replace("vídeos", "").replace("videos", "").strip()
    m = re.search(r"([\d\.,]+)\s*(mil|mi|milhão|milhões)?", s)
    if not m:
        return None
    numero, unidade = m.group(1), m.group(2)
    if "," in numero:
        numero = numero.replace(".", "").replace(",", ".")
    elif "." in numero:
        partes = numero.split(".")
        if len(partes[-1]) == 3 and unidade is None:
            numero = numero.replace(".", "")
    try:
        n = float(numero)
    except ValueError:
        return None
    if unidade == "mil":
        n *= 1_000
    elif unidade in ("mi", "milhão", "milhões"):
        n *= 1_000_000
    return int(round(n))


def data_iso_de_texto(texto, ano=2026):
    texto = corrigir_mojibake(texto).strip()
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})(?:/(\d{4}))?", texto)
    if m:
        d, mes, a = int(m.group(1)), int(m.group(2)), int(m.group(3) or ano)
        return f"{a:04d}-{mes:02d}-{d:02d}"
    meses = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }
    m = re.fullmatch(r"([A-Za-z]{3})\s+(\d{1,2}),\s*(\d{4})", texto)
    if m and m.group(1).lower() in meses:
        return f"{int(m.group(3)):04d}-{meses[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    return None


def coletar_kworb():
    print("\n" + "=" * 70)
    print("1. KWORB — TIKTOK TRENDING SONGS BRASIL")
    print("=" * 70)
    html = baixar(KWORB_URL, f"kworb_tiktok_br_{DATA_EXECUCAO}.html")
    tabelas = pd.read_html(StringIO(html))
    df = next((t.copy() for t in tabelas if any("Artist" in str(c) for c in t.columns)), None)
    if df is None:
        raise RuntimeError("Tabela TikTok do KWORB não encontrada.")
    df.columns = [str(c).strip() for c in df.columns]
    artista_col = next(c for c in df.columns if "Artist" in c)
    df = df.rename(columns={"Pos": "Posicao", "P+": "Variacao", artista_col: "Artista_Musica"})
    partes = df["Artista_Musica"].astype(str).str.split(" - ", n=1, expand=True)
    df["Artista"] = partes[0].map(corrigir_mojibake).str.strip()
    df["Musica"] = partes[1].map(corrigir_mojibake).str.strip() if partes.shape[1] > 1 else ""
    df["Posicao"] = pd.to_numeric(df["Posicao"], errors="coerce")
    df = df[df["Posicao"].notna()].copy()
    df["Posicao"] = df["Posicao"].astype(int)
    df["Data_Ranking"] = DATA_EXECUCAO
    df["Data_Execucao"] = DATA_EXECUCAO
    df["Plataforma"] = "TikTok"
    df["Fonte"] = "KWORB"
    df["Tipo_Ranking"] = "Trending"
    df["Pais"] = "Brasil"
    df["Artista_Normalizado"] = df["Artista"].map(normalizar)
    df = df[["Data_Ranking", "Data_Execucao", "Plataforma", "Fonte", "Tipo_Ranking", "Pais", "Posicao", "Variacao", "Artista", "Artista_Normalizado", "Musica"]]
    df.to_csv(os.path.join(PASTA_TRATADOS, "tiktok_kworb_brasil.csv"), index=False, encoding="utf-8-sig")
    print(f"✓ KWORB: {len(df)} registros tratados.")
    return df


def extrair_data_ranking(soup):
    for txt in soup.stripped_strings:
        iso = data_iso_de_texto(corrigir_mojibake(txt))
        if iso:
            return iso
    return DATA_EXECUCAO


def extrair_links_sons(soup):
    links = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/songs/" in href:
            titulo = corrigir_mojibake(a.get_text(" ", strip=True))
            if titulo:
                links[normalizar(titulo)] = urljoin(BASE_TTS, href)
    return links


def linhas_limpas(soup):
    return [corrigir_mojibake(x).strip() for x in soup.stripped_strings if corrigir_mojibake(x).strip()]


def coletar_chart_tts(url, tipo):
    print("\n" + "=" * 70)
    print(f"2. TRENDING TIKTOK SONGS — {tipo.upper()}")
    print("=" * 70)
    html = baixar(url, f"trending_tiktok_{tipo.lower()}_{DATA_EXECUCAO}.html")
    soup = BeautifulSoup(html, "html.parser")
    data_ranking = extrair_data_ranking(soup)
    links_sons = extrair_links_sons(soup)
    linhas = linhas_limpas(soup)
    registros = []
    for i, linha in enumerate(linhas):
        if not re.search(r"\b(vídeos|videos)\b", linha, flags=re.I) or not re.search(r"\d", linha):
            continue
        qtd = videos_para_int(linha)
        if qtd is None:
            continue
        anteriores = []
        j = i - 1
        while j >= 0 and len(anteriores) < 8:
            val = linhas[j].strip()
            if val not in ("·", "TikTok", "Spotify"):
                anteriores.append(val)
            j -= 1
        pos = None
        for val in anteriores:
            if re.fullmatch(r"\d{1,3}", val):
                n = int(val)
                if 1 <= n <= 50:
                    pos = n
                    break
        if pos is None or len(anteriores) < 2:
            continue
        artista = anteriores[0]
        musica = anteriores[1]
        lixo = {"tiktok", "spotify", "ranking", "rankings", "em alta", "virais", "popular", "viral"}
        if normalizar(artista) in lixo or normalizar(musica) in lixo:
            continue
        registros.append({
            "Data_Ranking": data_ranking,
            "Data_Execucao": DATA_EXECUCAO,
            "Plataforma": "TikTok",
            "Fonte": "TrendingTikTokSongs",
            "Tipo_Ranking": tipo,
            "Pais": "Brasil",
            "Posicao": pos,
            "Artista": artista,
            "Artista_Normalizado": normalizar(artista),
            "Musica": musica,
            "Videos_TikTok": qtd,
            "URL_Som": links_sons.get(normalizar(musica), ""),
        })
    df = pd.DataFrame(registros)
    if not df.empty:
        df = df.sort_values("Posicao").drop_duplicates(subset=["Tipo_Ranking", "Posicao"], keep="first").reset_index(drop=True)
    df.to_csv(os.path.join(PASTA_TRATADOS, f"tiktok_{tipo.lower()}_brasil.csv"), index=False, encoding="utf-8-sig")
    print(f"✓ {tipo}: {len(df)} posições estruturadas. Data da fonte: {data_ranking}")
    return df


def inteiro_en(texto):
    if texto is None:
        return None
    s = re.sub(r"[^\d.-]", "", str(texto).strip().replace(",", ""))
    if not s:
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def decimal_en(texto):
    if texto is None:
        return None
    s = re.sub(r"[^\d.+-]", "", str(texto).strip().replace(",", ""))
    try:
        return float(s) if s else None
    except ValueError:
        return None


def extrair_metrica_rotulo(linhas, rotulo):
    alvo = normalizar(rotulo)
    for i, linha in enumerate(linhas):
        if normalizar(linha) == alvo and i + 1 < len(linhas):
            return corrigir_mojibake(linhas[i + 1]).strip()
    return None


def extrair_resumo_som(linhas, url_som, musica, artista):
    raw_videos = extrair_metrica_rotulo(linhas, "TikTok videos")
    raw_uso_7d = extrair_metrica_rotulo(linhas, "7-day usage")
    raw_change = extrair_metrica_rotulo(linhas, "Change")
    raw_rank_7d = extrair_metrica_rotulo(linhas, "7-day rank")
    raw_peak_rank = extrair_metrica_rotulo(linhas, "Peak rank")
    raw_peak_date = extrair_metrica_rotulo(linhas, "Peak date")
    raw_streak = extrair_metrica_rotulo(linhas, "Current streak")
    raw_days = extrair_metrica_rotulo(linhas, "Days charting")
    raw_first = extrair_metrica_rotulo(linhas, "First seen")
    raw_latest = extrair_metrica_rotulo(linhas, "Latest seen")
    raw_countries = extrair_metrica_rotulo(linhas, "Countries")
    def primeiro_inteiro(v):
        if not v:
            return None
        m = re.search(r"[\d,]+", v)
        return inteiro_en(m.group(0)) if m else None
    pico = primeiro_inteiro(raw_peak_rank)
    return {
        "Artista": artista,
        "Musica": musica,
        "URL_Som": url_som,
        "Videos_TikTok_Atual": inteiro_en(raw_videos),
        "Uso_7D": primeiro_inteiro(raw_uso_7d),
        "Variacao_7D_Pct": decimal_en(raw_change),
        "Rank_7D_Texto": raw_rank_7d,
        "Pico_Posicao": pico,
        "Pico_Data": data_iso_de_texto(raw_peak_date) if raw_peak_date else None,
        "Sequencia_Atual_Dias": primeiro_inteiro(raw_streak),
        "Dias_no_Chart": primeiro_inteiro(raw_days),
        "Primeira_Aparicao": data_iso_de_texto(raw_first) if raw_first else None,
        "Ultima_Aparicao": data_iso_de_texto(raw_latest) if raw_latest else None,
        "Paises": primeiro_inteiro(raw_countries),
    }


def extrair_historico_som(url_som, musica, artista):
    html = baixar(url_som)
    soup = BeautifulSoup(html, "html.parser")
    linhas = linhas_limpas(soup)
    texto = re.sub(r"\s+", " ", corrigir_mojibake(soup.get_text(" ", strip=True)))
    registros = []
    padrao = re.compile(
        r"([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}).{0,80}?Rank\s*#\s*(\d+).{0,80}?TikTok\s+videos\s*[▲+]\s*([\d,]+)\s+([\d,]+)",
        flags=re.I,
    )
    for m in padrao.finditer(texto):
        data_txt, rank_txt, novos_txt, total_txt = m.groups()
        data = data_iso_de_texto(data_txt)
        if data:
            registros.append({
                "Data": data,
                "Artista": artista,
                "Musica": musica,
                "Rank": int(rank_txt),
                "Novos_Videos_TikTok": inteiro_en(novos_txt),
                "Videos_TikTok_Acumulados": inteiro_en(total_txt),
                "URL_Som": url_som,
            })
    historico = pd.DataFrame(registros)
    if not historico.empty:
        historico = historico.drop_duplicates(["Data", "URL_Som"]).sort_values(["URL_Som", "Data"])
    resumo = extrair_resumo_som(linhas, url_som, musica, artista)
    if resumo.get("Videos_TikTok_Atual") is None:
        m = re.search(r"At a glance.*?TikTok videos\s+([\d,]+)", texto, flags=re.I)
        if m:
            resumo["Videos_TikTok_Atual"] = inteiro_en(m.group(1))
    return historico, resumo


def coletar_historicos(popular, viral):
    charts = pd.concat([df for df in (popular, viral) if not df.empty], ignore_index=True)
    if charts.empty or "URL_Som" not in charts.columns:
        return pd.DataFrame(), pd.DataFrame()
    sons = charts[charts["URL_Som"].fillna("").str.len() > 0][["URL_Som", "Musica", "Artista"]].drop_duplicates("URL_Som")
    historicos, resumos = [], []
    for _, row in sons.iterrows():
        try:
            dfh, resumo = extrair_historico_som(row["URL_Som"], row["Musica"], row["Artista"])
            if not dfh.empty:
                historicos.append(dfh)
            resumos.append(resumo)
        except Exception as e:
            print(f"⚠ Histórico {row['Musica']}: {type(e).__name__}: {e}")
        time.sleep(0.15)
    historico = pd.concat(historicos, ignore_index=True) if historicos else pd.DataFrame()
    resumo = pd.DataFrame(resumos)
    historico.to_csv(os.path.join(PASTA_TRATADOS, "tiktok_historico_sons.csv"), index=False, encoding="utf-8-sig")
    resumo.to_csv(os.path.join(PASTA_TRATADOS, "tiktok_resumo_sons.csv"), index=False, encoding="utf-8-sig")
    print(f"✓ Histórico 7D: {len(historico)} registros; resumos: {len(resumo)}")
    return historico, resumo


def main():
    criar_pastas()
    print("=" * 70)
    print("COLETA DIÁRIA TIKTOK — ROCK IN RIO 2026")
    print("=" * 70)
    kworb = coletar_kworb()
    popular = coletar_chart_tts(POPULAR_URL, "Popular")
    viral = coletar_chart_tts(VIRAL_URL, "Viral")
    historico, resumo = coletar_historicos(popular, viral)
    resultado = {
        "data_execucao": DATA_EXECUCAO,
        "kworb": len(kworb),
        "popular": len(popular),
        "viral": len(viral),
        "historico_7d": len(historico),
        "resumos": len(resumo),
    }
    with open(os.path.join(PASTA_TRATADOS, "validacao_tiktok.json"), "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(resultado)


if __name__ == "__main__":
    main()
