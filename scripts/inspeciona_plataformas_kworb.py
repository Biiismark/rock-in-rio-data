from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


URL = "https://kworb.net/"

CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
}

PALAVRAS = [
    "spotify",
    "apple",
    "itunes",
    "deezer",
    "youtube",
]


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

    sopa = BeautifulSoup(resposta.text, "lxml")
    encontrados = set()

    for link in sopa.find_all("a", href=True):
        texto = link.get_text(" ", strip=True)
        endereco = urljoin(URL, link["href"])

        conteudo = f"{texto} {endereco}".lower()

        if any(
            palavra in conteudo
            for palavra in PALAVRAS
        ):
            encontrados.add(
                (
                    texto or "(sem título)",
                    endereco,
                )
            )

    print("PLATAFORMAS E LINKS ENCONTRADOS NO KWORB\n")

    for texto, endereco in sorted(encontrados):
        print(f"{texto}: {endereco}")

    print(
        f"\nTotal de links relacionados: "
        f"{len(encontrados)}"
    )


if __name__ == "__main__":
    main()