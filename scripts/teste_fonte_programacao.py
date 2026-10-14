from pathlib import Path
import requests

URL = "https://rockinrio.com/rio/pt-br/line-up/"

cabecalhos = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
}

arquivo_saida = Path("dados/brutos/lineup_oficial.html")

try:
    resposta = requests.get(URL, headers=cabecalhos, timeout=30)
    resposta.raise_for_status()

    arquivo_saida.write_text(resposta.text, encoding="utf-8")

    print(f"Status HTTP: {resposta.status_code}")
    print(f"Caracteres recebidos: {len(resposta.text):,}")
    print(f"Arquivo salvo em: {arquivo_saida}")

    for termo in ["Palco Mundo", "Line-up", "line-up"]:
        encontrado = termo.lower() in resposta.text.lower()
        print(f"'{termo}' encontrado no HTML: {encontrado}")

except requests.RequestException as erro:
    print("Não foi possível acessar a fonte oficial.")
    print(f"Detalhe: {erro}")