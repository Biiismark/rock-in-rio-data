from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo
import mimetypes
import re
import shutil
import time
import unicodedata

import pandas as pd
import requests
from bs4 import BeautifulSoup


FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")

PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_REFERENCIAS = PASTA_PROJETO / "dados" / "referencias"
PASTA_BRUTOS = PASTA_PROJETO / "dados" / "brutos" / "perfis_artistas_rir"
PASTA_FOTOS = PASTA_PROJETO / "assets" / "artistas"

ARQUIVO_ARTISTAS = PASTA_REFERENCIAS / "artistas.csv"
ARQUIVO_AUDITORIA = PASTA_REFERENCIAS / "auditoria_perfis_artistas_rir.csv"

CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

EXTENSOES_POR_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def limpar_texto(texto):
    if texto is None or pd.isna(texto):
        return ""

    # NFC preserva caracteres tipográficos significativos, como o indicador
    # ordinal em “31º”, sem reintroduzir caracteres invisíveis.
    texto = unicodedata.normalize("NFC", str(texto))
    texto = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def caminho_relativo(caminho):
    return str(
        caminho.resolve().relative_to(PASTA_PROJETO.resolve())
    ).replace("\\", "/")


def obter_url_imagem(sopa, url_pagina, url_existente):
    imagem = sopa.select_one(".bloco-artista img.img-banda")

    if imagem:
        for atributo in ["src", "data-src", "data-lazy-src"]:
            valor = limpar_texto(imagem.get(atributo))

            if valor:
                return urljoin(url_pagina, valor)

        srcset = limpar_texto(imagem.get("srcset"))

        if srcset:
            ultima_opcao = srcset.split(",")[-1].strip().split(" ")[0]
            return urljoin(url_pagina, ultima_opcao)

    meta_imagem = sopa.select_one(
        'meta[property="og:image"], meta[name="twitter:image"]'
    )

    if meta_imagem:
        valor = limpar_texto(meta_imagem.get("content"))

        if valor:
            return urljoin(url_pagina, valor)

    return limpar_texto(url_existente)


def extrair_bio(sopa):
    descricao = sopa.select_one(".bloco-artista .descricao")

    if descricao is None:
        return "", 0

    paragrafos = []

    for paragrafo in descricao.select("p"):
        texto = limpar_texto(paragrafo.get_text(" ", strip=True))

        if texto:
            paragrafos.append(texto)

    if not paragrafos:
        texto = limpar_texto(descricao.get_text(" ", strip=True))

        if texto:
            paragrafos.append(texto)

    return "\n\n".join(paragrafos), len(paragrafos)


def determinar_extensao(url_imagem, tipo_conteudo):
    tipo_conteudo = limpar_texto(tipo_conteudo).split(";")[0].lower()

    if tipo_conteudo in EXTENSOES_POR_MIME:
        return EXTENSOES_POR_MIME[tipo_conteudo]

    extensao = Path(urlparse(url_imagem).path).suffix.lower()

    if extensao in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ".jpg" if extensao == ".jpeg" else extensao

    extensao_mime = mimetypes.guess_extension(tipo_conteudo)
    return extensao_mime or ".jpg"


def baixar_imagem(sessao, url_imagem, nome_base):
    if not url_imagem:
        raise ValueError("URL da imagem não encontrada.")

    resposta = sessao.get(url_imagem, timeout=45)
    resposta.raise_for_status()

    tipo_conteudo = resposta.headers.get("Content-Type", "")

    if tipo_conteudo and not tipo_conteudo.lower().startswith("image/"):
        raise ValueError(
            f"O endereço retornou conteúdo não visual: {tipo_conteudo}"
        )

    if len(resposta.content) < 1_000:
        raise ValueError("A imagem recebida é pequena demais ou está vazia.")

    extensao = determinar_extensao(url_imagem, tipo_conteudo)
    arquivo_foto = PASTA_FOTOS / f"{nome_base}{extensao}"
    arquivo_foto.write_bytes(resposta.content)

    return arquivo_foto, len(resposta.content)


def criar_backup(agora):
    nome_backup = (
        "artistas_antes_perfis_"
        + agora.strftime("%Y-%m-%d_%H-%M-%S")
        + ".csv"
    )

    arquivo_backup = PASTA_REFERENCIAS / nome_backup
    shutil.copy2(ARQUIVO_ARTISTAS, arquivo_backup)
    return arquivo_backup


def garantir_colunas(dados):
    colunas = [
        "foto_url_original",
        "foto_arquivo_local",
        "foto_url_publica",
        "foto_credito",
        "bio_fonte_url",
        "bio_credito",
        "bio_coletada_em",
        "html_arquivo_local",
    ]

    for coluna in colunas:
        if coluna not in dados.columns:
            dados[coluna] = ""

    return dados


def main():
    agora = datetime.now(FUSO_BRASIL)
    coletado_em = agora.isoformat(timespec="seconds")

    print("COLETANDO FOTOS E BIOS OFICIAIS DO ROCK IN RIO")

    if not ARQUIVO_ARTISTAS.exists():
        raise FileNotFoundError(
            f"Cadastro de artistas não encontrado: {ARQUIVO_ARTISTAS}"
        )

    PASTA_BRUTOS.mkdir(parents=True, exist_ok=True)
    PASTA_FOTOS.mkdir(parents=True, exist_ok=True)
    PASTA_REFERENCIAS.mkdir(parents=True, exist_ok=True)

    artistas = pd.read_csv(
        ARQUIVO_ARTISTAS,
        encoding="utf-8-sig",
        dtype=str,
        keep_default_na=False,
    )

    obrigatorias = {
        "artista_id",
        "nome_artista",
        "foto_url",
        "bio_curta",
        "url_pagina_artista",
    }

    ausentes = sorted(obrigatorias - set(artistas.columns))

    if ausentes:
        raise ValueError(
            "Colunas ausentes em artistas.csv: " + ", ".join(ausentes)
        )

    artistas = garantir_colunas(artistas)
    arquivo_backup = criar_backup(agora)

    sessao = requests.Session()
    sessao.headers.update(CABECALHOS)

    auditoria = []
    total = len(artistas)

    for indice, linha in artistas.iterrows():
        artista_id = limpar_texto(linha["artista_id"])
        nome_artista = limpar_texto(linha["nome_artista"])
        url_pagina = limpar_texto(linha["url_pagina_artista"])

        print(f"[{indice + 1}/{total}] {nome_artista}")

        registro_auditoria = {
            "coletado_em": coletado_em,
            "artista_id": artista_id,
            "nome_artista": nome_artista,
            "url_pagina_artista": url_pagina,
            "status_pagina": "erro",
            "status_bio": "não extraída",
            "status_foto": "não baixada",
            "quantidade_paragrafos": 0,
            "caracteres_bio": 0,
            "bytes_foto": 0,
            "erro": "",
        }

        try:
            if not url_pagina:
                raise ValueError("Artista sem URL da página oficial.")

            resposta = sessao.get(url_pagina, timeout=45)
            resposta.raise_for_status()

            arquivo_html = PASTA_BRUTOS / f"{artista_id}.html"
            arquivo_html.write_bytes(resposta.content)

            sopa = BeautifulSoup(resposta.content, "lxml")
            bio, quantidade_paragrafos = extrair_bio(sopa)

            url_imagem = obter_url_imagem(
                sopa=sopa,
                url_pagina=url_pagina,
                url_existente=linha.get("foto_url", ""),
            )

            artistas.at[indice, "html_arquivo_local"] = caminho_relativo(
                arquivo_html
            )
            artistas.at[indice, "bio_fonte_url"] = url_pagina
            artistas.at[indice, "bio_credito"] = "Rock in Rio"
            artistas.at[indice, "bio_coletada_em"] = coletado_em
            artistas.at[indice, "foto_credito"] = "Rock in Rio"

            registro_auditoria["status_pagina"] = "baixada"

            if bio:
                artistas.at[indice, "bio_curta"] = bio
                registro_auditoria["status_bio"] = "extraída"
                registro_auditoria["quantidade_paragrafos"] = (
                    quantidade_paragrafos
                )
                registro_auditoria["caracteres_bio"] = len(bio)

            else:
                registro_auditoria["status_bio"] = "seção não encontrada"

            if url_imagem:
                nome_base = artista_id.removeprefix("art_")
                arquivo_foto, bytes_foto = baixar_imagem(
                    sessao=sessao,
                    url_imagem=url_imagem,
                    nome_base=nome_base,
                )

                artistas.at[indice, "foto_url"] = url_imagem
                artistas.at[indice, "foto_url_original"] = url_imagem
                artistas.at[indice, "foto_arquivo_local"] = caminho_relativo(
                    arquivo_foto
                )

                registro_auditoria["status_foto"] = "baixada"
                registro_auditoria["bytes_foto"] = bytes_foto

            print(
                "   "
                f"Página: {registro_auditoria['status_pagina']} | "
                f"Bio: {registro_auditoria['status_bio']} | "
                f"Foto: {registro_auditoria['status_foto']}"
            )

        except (requests.RequestException, ValueError, OSError) as erro:
            registro_auditoria["erro"] = str(erro)
            print(f"   ERRO: {erro}")

        auditoria.append(registro_auditoria)
        time.sleep(0.4)

    artistas.to_csv(
        ARQUIVO_ARTISTAS,
        index=False,
        encoding="utf-8-sig",
    )

    auditoria_df = pd.DataFrame(auditoria)
    auditoria_df.to_csv(
        ARQUIVO_AUDITORIA,
        index=False,
        encoding="utf-8-sig",
    )

    paginas_baixadas = int(
        (auditoria_df["status_pagina"] == "baixada").sum()
    )
    bios_extraidas = int(
        (auditoria_df["status_bio"] == "extraída").sum()
    )
    fotos_baixadas = int(
        (auditoria_df["status_foto"] == "baixada").sum()
    )
    erros = int((auditoria_df["erro"] != "").sum())

    print("\nCOLETA DE PERFIS CONCLUÍDA")
    print(f"Artistas analisados: {total}")
    print(f"Páginas preservadas: {paginas_baixadas}")
    print(f"Bios extraídas: {bios_extraidas}")
    print(f"Fotos baixadas: {fotos_baixadas}")
    print(f"Erros: {erros}")

    print(f"\nCadastro atualizado: {ARQUIVO_ARTISTAS}")
    print(f"Backup anterior: {arquivo_backup}")
    print(f"Auditoria: {ARQUIVO_AUDITORIA}")
    print(f"HTMLs: {PASTA_BRUTOS}")
    print(f"Fotos: {PASTA_FOTOS}")

    if bios_extraidas != total or fotos_baixadas != total:
        print(
            "\nATENÇÃO: algum perfil ficou incompleto. "
            "Consulte a auditoria antes de usar as imagens no Power BI."
        )


if __name__ == "__main__":
    main()
