from pathlib import Path
import re
import unicodedata

import pandas as pd
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode


PALCO_DESEJADO = "Palco Mundo"

DIAS = {
    "2026-09-04": "04-set",
    "2026-09-05": "05-set",
    "2026-09-06": "06-set",
    "2026-09-07": "07-set",
    "2026-09-11": "11-set",
    "2026-09-12": "12-set",
    "2026-09-13": "13-set",
}

CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
}

PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_BRUTOS = PASTA_PROJETO / "dados" / "brutos"
PASTA_REFERENCIAS = PASTA_PROJETO / "dados" / "referencias"
PASTA_METODOLOGIA = PASTA_PROJETO / "dados" / "metodologia"

PASTA_BRUTOS.mkdir(parents=True, exist_ok=True)
PASTA_REFERENCIAS.mkdir(parents=True, exist_ok=True)
PASTA_METODOLOGIA.mkdir(parents=True, exist_ok=True)


def limpar_texto(texto):
    """Remove caracteres invisíveis e espaços desnecessários."""
    texto = unicodedata.normalize("NFKC", texto)
    texto = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def normalizar_nome(nome):
    """Cria uma versão padronizada do nome para identificadores."""
    nome = limpar_texto(nome)
    nome = unidecode(nome).lower()
    nome = re.sub(r"[^a-z0-9]+", "_", nome)
    return nome.strip("_")


def buscar_pagina(url):
    """Baixa o HTML de uma página oficial."""
    resposta = requests.get(url, headers=CABECALHOS, timeout=30)
    resposta.raise_for_status()
    resposta.encoding = "utf-8"
    return resposta.text


def extrair_palco_mundo(html, data_evento, url_fonte):
    """Extrai somente as apresentações do Palco Mundo."""
    sopa = BeautifulSoup(html, "lxml")
    palco_atual = None
    registros = []

    blocos = sopa.select("section.resultado .bloco-artista")
    for bloco in blocos:
        titulo_palco = bloco.select_one("div.data > span")
        if titulo_palco:
            palco_atual = limpar_texto(titulo_palco.get_text(" ", strip=True))
            continue

        if palco_atual != PALCO_DESEJADO:
            continue

        for item in bloco.select("div.item"):
            titulo = item.select_one("h2")
            link = item.select_one("a")
            if not titulo or not link:
                continue

            nome_artista = limpar_texto(titulo.get_text(" ", strip=True))
            artista_id = f"art_{normalizar_nome(nome_artista)}"
            foto_url = item.get("data-image-url", "").replace("http://", "https://", 1)

            registros.append(
                {
                    "apresentacao_id": f"apr_{data_evento.replace('-', '')}_{artista_id}",
                    "artista_id": artista_id,
                    "nome_artista": nome_artista,
                    "data": data_evento,
                    "horario": "",
                    "palco": palco_atual,
                    "url_fonte": url_fonte,
                    "url_pagina_artista": link.get("href", ""),
                    "foto_url": foto_url,
                }
            )

    return registros


def aplicar_horarios_auditados(programacao):
    """Preserva horários validados manualmente ao regenerar a programação.

    O arquivo auditado é separado porque a página oficial usada pela coleta
    estruturada nem sempre expõe o horário. O dado de 'data' permanece sendo
    a data/festival day; a data civil real, inclusive viradas após meia-noite,
    fica documentada no arquivo metodológico de horários auditados.
    """
    candidatos = sorted(PASTA_METODOLOGIA.glob("programacao_horarios_auditados_*.csv"))
    if not candidatos:
        print("AVISO: nenhum arquivo de horários auditados encontrado; mantendo horario vazio.")
        return programacao

    arquivo = candidatos[-1]
    auditada = pd.read_csv(arquivo, encoding="utf-8-sig", dtype=str).fillna("")
    necessarias = {"apresentacao_id", "horario_inicio"}
    if not necessarias.issubset(auditada.columns):
        print(f"AVISO: {arquivo.name} não possui as colunas esperadas; mantendo horario vazio.")
        return programacao

    mapa = (
        auditada[["apresentacao_id", "horario_inicio"]]
        .drop_duplicates("apresentacao_id", keep="last")
        .set_index("apresentacao_id")["horario_inicio"]
        .to_dict()
    )
    programacao["horario"] = programacao["apresentacao_id"].map(mapa).fillna(programacao["horario"])
    preenchidos = int(programacao["horario"].astype(str).str.len().gt(0).sum())
    print(f"Horários auditados aplicados: {preenchidos}/{len(programacao)} | fonte: {arquivo.name}")
    return programacao


def main():
    todas_apresentacoes = []

    for data_evento, slug_dia in DIAS.items():
        url = "https://rockinrio.com/rio/" f"line-up/dia/{slug_dia}/"
        print(f"\nColetando {data_evento}...")

        try:
            html = buscar_pagina(url)
        except requests.RequestException as erro:
            print(f"ERRO ao acessar {url}: {erro}")
            continue

        arquivo_bruto = PASTA_BRUTOS / f"lineup_{slug_dia}.html"
        arquivo_bruto.write_text(html, encoding="utf-8")

        registros = extrair_palco_mundo(html=html, data_evento=data_evento, url_fonte=url)
        todas_apresentacoes.extend(registros)
        print("Apresentações do Palco Mundo encontradas: " f"{len(registros)}")

    if not todas_apresentacoes:
        print("\nNenhuma apresentação foi encontrada. Verifique a estrutura da fonte.")
        return

    programacao = pd.DataFrame(todas_apresentacoes)
    programacao = aplicar_horarios_auditados(programacao)

    artistas = (
        programacao[["artista_id", "nome_artista", "foto_url", "url_pagina_artista"]]
        .drop_duplicates(subset="artista_id")
        .copy()
    )
    artistas["nome_normalizado"] = artistas["nome_artista"].apply(normalizar_nome)
    artistas["genero"] = ""
    artistas["pais"] = ""
    artistas["bio_curta"] = ""
    artistas = artistas[
        [
            "artista_id", "nome_artista", "nome_normalizado", "genero", "pais",
            "foto_url", "bio_curta", "url_pagina_artista",
        ]
    ]

    programacao = programacao[
        ["apresentacao_id", "artista_id", "nome_artista", "data", "horario", "palco", "url_fonte"]
    ]

    arquivo_artistas = PASTA_REFERENCIAS / "artistas.csv"
    arquivo_programacao = PASTA_REFERENCIAS / "programacao.csv"

    artistas.to_csv(arquivo_artistas, index=False, encoding="utf-8-sig")
    programacao.to_csv(arquivo_programacao, index=False, encoding="utf-8-sig")

    print("\nCOLETA CONCLUÍDA")
    print(f"Total de apresentações: {len(programacao)}")
    print(f"Total de artistas únicos: {len(artistas)}")
    print("\nArtistas encontrados:")
    for nome in artistas["nome_artista"]:
        print(f" - {nome}")
    print(f"\nArquivo criado: {arquivo_artistas}")
    print(f"Arquivo criado: {arquivo_programacao}")


if __name__ == "__main__":
    main()
