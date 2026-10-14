from io import StringIO
from pathlib import Path

import pandas as pd
import requests


URL = "https://kworb.net/spotify/country/br_daily.html"

CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
}

PASTA_PROJETO = Path(__file__).resolve().parents[1]
ARQUIVO_HTML = (
    PASTA_PROJETO
    / "dados"
    / "brutos"
    / "kworb_spotify_br_teste.html"
)


def main():
    try:
        resposta = requests.get(
            URL,
            headers=CABECALHOS,
            timeout=30,
        )

        resposta.raise_for_status()
        resposta.encoding = "utf-8"

    except requests.RequestException as erro:
        print("Não foi possível acessar o Kworb.")
        print(f"Detalhe: {erro}")
        return

    ARQUIVO_HTML.write_text(
        resposta.text,
        encoding="utf-8",
    )

    print(f"Status HTTP: {resposta.status_code}")
    print(f"Caracteres recebidos: {len(resposta.text):,}")
    print(f"HTML salvo em: {ARQUIVO_HTML}")

    try:
        tabelas = pd.read_html(StringIO(resposta.text))

    except ValueError:
        print("Nenhuma tabela foi encontrada no HTML.")
        return

    print(f"Tabelas encontradas: {len(tabelas)}")

    for numero, tabela in enumerate(tabelas, start=1):
        print(f"\nTabela {numero}")
        print(f"Linhas: {len(tabela)}")
        print(f"Colunas: {tabela.columns.tolist()}")
        print(tabela.head(3).to_string(index=False))


if __name__ == "__main__":
    main()