from datetime import datetime
from hashlib import sha1
from io import StringIO
from pathlib import Path
from zoneinfo import ZoneInfo
import re
import unicodedata

import pandas as pd
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode


FONTES = {
    "itunes_musicas": {
        "url": "https://kworb.net/charts/itunes/br.html",
        "plataforma": "iTunes",
        "tipo_item": "Música",
        "periodicidade": "Snapshot diário",
        "coluna_item": "Artist - Title",
    },
    "apple_music_musicas": {
        "url": "https://kworb.net/charts/apple_s/br.html",
        "plataforma": "Apple Music",
        "tipo_item": "Música",
        "periodicidade": "Snapshot diário",
        "coluna_item": "Artist - Title",
    },
    "apple_music_albuns": {
        "url": "https://kworb.net/charts/apple_a/br.html",
        "plataforma": "Apple Music",
        "tipo_item": "Álbum",
        "periodicidade": "Snapshot diário",
        "coluna_item": "Artist - Title",
    },
    "itunes_albuns": {
        "url": "https://kworb.net/charts/aitunes/br.html",
        "plataforma": "iTunes",
        "tipo_item": "Álbum",
        "periodicidade": "Snapshot diário",
        "coluna_item": "Artist - Title",
    },
    "shazam_musicas": {
        "url": "https://kworb.net/charts/shazam/br.html",
        "plataforma": "Shazam",
        "tipo_item": "Música",
        "periodicidade": "Snapshot diário",
        "coluna_item": "Artist - Title",
    },
    "deezer_musicas": {
        "url": "https://kworb.net/charts/deezer/br.html",
        "plataforma": "Deezer",
        "tipo_item": "Música",
        "periodicidade": "Snapshot diário",
        "coluna_item": "Artist - Title",
    },
    "youtube_diario": {
        "url": "https://kworb.net/youtube/insights/br_daily.html",
        "plataforma": "YouTube",
        "tipo_item": "Música/Vídeo",
        "periodicidade": "Diária",
        "coluna_item": "Track",
    },
    "youtube_semanal": {
        "url": "https://kworb.net/youtube/insights/br.html",
        "plataforma": "YouTube",
        "tipo_item": "Música/Vídeo",
        "periodicidade": "Semanal",
        "coluna_item": "Track",
    },
}

CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
}

FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")

PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_BRUTOS = PASTA_PROJETO / "dados" / "brutos" / "charts_brasil"
PASTA_TRATADOS = PASTA_PROJETO / "dados" / "tratados"

ARQUIVO_HISTORICO = (
    PASTA_TRATADOS / "charts_brasil_diario.csv"
)

PASTA_BRUTOS.mkdir(parents=True, exist_ok=True)
PASTA_TRATADOS.mkdir(parents=True, exist_ok=True)


def limpar_texto(texto):
    if texto is None or pd.isna(texto):
        return ""

    texto = unicodedata.normalize(
        "NFKC",
        str(texto),
    )

    texto = re.sub(
        r"[\u200b\u200c\u200d\ufeff]",
        "",
        texto,
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto.strip()


def normalizar_texto(texto):
    texto = limpar_texto(texto)
    texto = unidecode(texto).lower()

    texto = re.sub(
        r"[^a-z0-9]+",
        "_",
        texto,
    )

    return texto.strip("_")


def converter_inteiro(valor):
    valor = limpar_texto(valor)

    if valor in {"", "-", "—", "nan"}:
        return None

    valor = valor.replace(",", "")
    valor = valor.replace(".", "")

    try:
        return int(valor)

    except ValueError:
        return None


def separar_artista_titulo(texto):
    texto = limpar_texto(texto)

    if " - " not in texto:
        return texto, ""

    artista, titulo = texto.split(
        " - ",
        1,
    )

    return (
        limpar_texto(artista),
        limpar_texto(titulo),
    )


def criar_item_id(
    plataforma,
    tipo_item,
    artista,
    titulo,
):
    base = "|".join(
        [
            normalizar_texto(plataforma),
            normalizar_texto(tipo_item),
            normalizar_texto(artista),
            normalizar_texto(titulo),
        ]
    )

    return sha1(
        base.encode("utf-8")
    ).hexdigest()[:20]


def extrair_data_fonte(
    sopa,
    data_coleta,
):
    titulo = sopa.select_one(".pagetitle")

    texto_titulo = (
        limpar_texto(
            titulo.get_text(
                " ",
                strip=True,
            )
        )
        if titulo
        else ""
    )

    resultado = re.search(
        r"(\d{4})/(\d{2})/(\d{2})",
        texto_titulo,
    )

    if resultado:
        ano, mes, dia = resultado.groups()

        return (
            f"{ano}-{mes}-{dia}",
            "Data publicada pela fonte",
            texto_titulo,
        )

    return (
        data_coleta,
        "Snapshot da coleta",
        texto_titulo,
    )


def baixar_pagina(url):
    resposta = requests.get(
        url,
        headers=CABECALHOS,
        timeout=30,
    )

    resposta.raise_for_status()
    resposta.encoding = "utf-8"

    return resposta.text


def extrair_fonte(
    nome_fonte,
    configuracao,
    coletado_em,
    data_coleta,
):
    html = baixar_pagina(
        configuracao["url"]
    )

    sopa = BeautifulSoup(
        html,
        "lxml",
    )

    (
        data_referencia,
        tipo_data,
        titulo_fonte,
    ) = extrair_data_fonte(
        sopa=sopa,
        data_coleta=data_coleta,
    )

    tabelas = pd.read_html(
        StringIO(html)
    )

    if not tabelas:
        raise ValueError(
            f"Nenhuma tabela encontrada em {nome_fonte}."
        )

    tabela = tabelas[0]
    registros = []

    for _, linha in tabela.iterrows():
        posicao = converter_inteiro(
            linha.get("Pos")
        )

        if posicao is None:
            continue

        item_bruto = limpar_texto(
            linha.get(
                configuracao["coluna_item"]
            )
        )

        artista, titulo = separar_artista_titulo(
            item_bruto
        )

        item_id = criar_item_id(
            plataforma=configuracao["plataforma"],
            tipo_item=configuracao["tipo_item"],
            artista=artista,
            titulo=titulo,
        )

        vezes_pico_texto = limpar_texto(
            linha.get("(x?)")
        )

        resultado_vezes_pico = re.search(
            r"x(\d+)",
            vezes_pico_texto,
        )

        vezes_pico = (
            int(resultado_vezes_pico.group(1))
            if resultado_vezes_pico
            else None
        )

        registros.append(
            {
                "data_referencia": data_referencia,
                "tipo_data": tipo_data,
                "data_coleta": data_coleta,
                "coletado_em": coletado_em,
                "fonte": nome_fonte,
                "plataforma": configuracao["plataforma"],
                "pais": "Brasil",
                "tipo_item": configuracao["tipo_item"],
                "periodicidade": configuracao["periodicidade"],
                "item_id": item_id,
                "artista": artista,
                "artista_normalizado": normalizar_texto(
                    artista
                ),
                "titulo": titulo,
                "titulo_normalizado": normalizar_texto(
                    titulo
                ),
                "item_bruto": item_bruto,
                "posicao": posicao,
                "movimento_posicao": limpar_texto(
                    linha.get("P+")
                ),
                "semanas_no_ranking": converter_inteiro(
                    linha.get("Wks")
                ),
                "pico": converter_inteiro(
                    linha.get("Pk")
                ),
                "vezes_no_pico": vezes_pico,
                "valor_fonte": converter_inteiro(
                    linha.get("Streams")
                ),
                "variacao_valor_fonte": converter_inteiro(
                    linha.get("Streams+")
                ),
                "titulo_fonte": titulo_fonte,
                "url_fonte": configuracao["url"],
            }
        )

    arquivo_html = (
        PASTA_BRUTOS
        / f"{nome_fonte}_{data_referencia}.html"
    )

    arquivo_html.write_text(
        html,
        encoding="utf-8",
    )

    return pd.DataFrame(registros)


def tratar_duplicidades(novos_dados):
    chaves = [
        "data_referencia",
        "fonte",
        "item_id",
    ]

    mascara_duplicados = novos_dados.duplicated(
        subset=chaves,
        keep=False,
    )

    duplicados = novos_dados[
        mascara_duplicados
    ].copy()

    quantidade_removida = (
        len(novos_dados)
        - len(
            novos_dados.drop_duplicates(
                subset=chaves
            )
        )
    )

    if not duplicados.empty:
        print("\nALERTA DE QUALIDADE")

        print(
            "A fonte publicou itens repetidos. "
            "A melhor posição será preservada."
        )

        for fonte, grupo in duplicados.groupby(
            "fonte"
        ):
            print(
                f" - {fonte}: "
                f"{len(grupo)} linhas envolvidas"
            )

            for _, linha in grupo.sort_values(
                "posicao"
            ).iterrows():
                print(
                    f"   posição {linha['posicao']}: "
                    f"{linha['item_bruto']}"
                )

    dados_unicos = (
        novos_dados
        .sort_values(
            [
                "data_referencia",
                "fonte",
                "item_id",
                "posicao",
            ]
        )
        .drop_duplicates(
            subset=chaves,
            keep="first",
        )
        .reset_index(drop=True)
    )

    return (
        dados_unicos,
        quantidade_removida,
    )


def substituir_snapshots(
    historico,
    novos_dados,
):
    snapshots_novos = (
        novos_dados[
            [
                "data_referencia",
                "fonte",
            ]
        ]
        .drop_duplicates()
        .assign(substituir_snapshot=True)
    )

    historico = historico.merge(
        snapshots_novos,
        on=[
            "data_referencia",
            "fonte",
        ],
        how="left",
    )

    historico = historico[
        historico["substituir_snapshot"].isna()
    ].drop(
        columns=["substituir_snapshot"]
    )

    return historico


def atualizar_historico(novos_dados):
    (
        novos_dados_unicos,
        duplicidades_removidas,
    ) = tratar_duplicidades(
        novos_dados
    )

    if ARQUIVO_HISTORICO.exists():
        historico = pd.read_csv(
            ARQUIVO_HISTORICO,
            encoding="utf-8-sig",
            dtype={
                "data_referencia": str,
                "data_coleta": str,
            },
        )

        historico = substituir_snapshots(
            historico=historico,
            novos_dados=novos_dados_unicos,
        )

        resultado = pd.concat(
            [
                historico,
                novos_dados_unicos,
            ],
            ignore_index=True,
        )

    else:
        resultado = novos_dados_unicos.copy()

    resultado = (
        resultado
        .sort_values(
            [
                "data_referencia",
                "plataforma",
                "tipo_item",
                "fonte",
                "posicao",
            ]
        )
        .reset_index(drop=True)
    )

    resultado.to_csv(
        ARQUIVO_HISTORICO,
        index=False,
        encoding="utf-8-sig",
    )

    return (
        resultado,
        novos_dados_unicos,
        duplicidades_removidas,
    )


def main():
    agora = datetime.now(
        FUSO_BRASIL
    )

    coletado_em = agora.isoformat(
        timespec="seconds"
    )

    data_coleta = agora.date().isoformat()

    todos_dados = []

    print("COLETANDO CHARTS DO BRASIL")

    for nome_fonte, configuracao in FONTES.items():
        print(f"\nColetando {nome_fonte}...")

        try:
            dados = extrair_fonte(
                nome_fonte=nome_fonte,
                configuracao=configuracao,
                coletado_em=coletado_em,
                data_coleta=data_coleta,
            )

        except requests.RequestException as erro:
            print(f"ERRO DE ACESSO: {erro}")
            continue

        except (ValueError, KeyError) as erro:
            print(f"ERRO DE LEITURA: {erro}")
            continue

        todos_dados.append(dados)

        data_fonte = (
            dados["data_referencia"].iloc[0]
            if not dados.empty
            else "sem data"
        )

        print(
            f"Registros brutos: {len(dados)} | "
            f"Referência: {data_fonte}"
        )

    if not todos_dados:
        print(
            "\nNenhuma fonte retornou dados."
        )
        return

    novos_dados = pd.concat(
        todos_dados,
        ignore_index=True,
    )

    (
        historico,
        novos_dados_unicos,
        duplicidades_removidas,
    ) = atualizar_historico(
        novos_dados
    )

    print("\nCOLETA CONCLUÍDA")

    print(
        f"Registros brutos coletados: "
        f"{len(novos_dados)}"
    )

    print(
        f"Registros únicos coletados: "
        f"{len(novos_dados_unicos)}"
    )

    print(
        f"Duplicidades da fonte removidas: "
        f"{duplicidades_removidas}"
    )

    print(
        f"Registros acumulados: "
        f"{len(historico)}"
    )

    print("\nResumo da coleta:")

    resumo = (
        novos_dados_unicos
        .groupby(
            [
                "plataforma",
                "tipo_item",
                "periodicidade",
                "data_referencia",
            ],
            as_index=False,
        )
        .size()
    )

    print(
        resumo.to_string(
            index=False
        )
    )

    print(
        f"\nArquivo salvo em: "
        f"{ARQUIVO_HISTORICO}"
    )


if __name__ == "__main__":
    main()