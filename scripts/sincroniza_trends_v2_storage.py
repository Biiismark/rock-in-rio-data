# -*- coding: utf-8 -*-
"""Publica somente os CSVs Google Trends V2 no Storage público do Supabase."""
from pathlib import Path
from urllib.parse import quote
import os
import time
import requests
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[1]
TRATADOS = RAIZ / "dados" / "tratados"
BUCKET = "powerbi"
PREFIXO = "google_trends_v2_"


def config():
    load_dotenv(RAIZ / ".env")
    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    key = os.getenv("SUPABASE_SECRET_KEY", "").strip()
    if not url or not key:
        raise RuntimeError("SUPABASE_URL/SUPABASE_SECRET_KEY ausentes.")
    return url, key


def enviar(url, key, path):
    remoto = f"tratados/{path.name}"
    cod = "/".join(quote(p, safe="") for p in remoto.split("/"))
    endpoint = f"{url}/storage/v1/object/{BUCKET}/{cod}"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "text/csv; charset=utf-8",
        "Cache-Control": "900",
        "x-upsert": "true",
    }
    last = None
    for tentativa in range(1, 4):
        try:
            with path.open("rb") as f:
                r = requests.post(endpoint, headers=headers, data=f, timeout=(30, 180))
            if r.status_code not in {200, 201}:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
            print("OK", path.name)
            return
        except Exception as exc:
            last = exc
            if tentativa < 3:
                time.sleep(5 * tentativa)
    raise RuntimeError(f"Falha em {path.name}: {last}")


def main():
    url, key = config()
    arquivos = sorted(TRATADOS.glob(f"{PREFIXO}*.csv"))
    if not arquivos:
        raise FileNotFoundError("Nenhum CSV Trends V2 em dados/tratados.")
    for p in arquivos:
        enviar(url, key, p)
    print(f"Publicados {len(arquivos)} arquivos Trends V2.")


if __name__ == "__main__":
    main()
