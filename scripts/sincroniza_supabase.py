from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo
import mimetypes
import os
import time

import pandas as pd
import requests
from dotenv import load_dotenv
from supabase import Client, create_client


FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")
PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_TRATADOS = PASTA_PROJETO / "dados" / "tratados"
PASTA_REFERENCIAS = PASTA_PROJETO / "dados" / "referencias"
PASTA_METODOLOGIA = PASTA_PROJETO / "dados" / "metodologia"
PASTA_FOTOS = PASTA_PROJETO / "assets" / "artistas"

ARQUIVO_ARTISTAS = PASTA_REFERENCIAS / "artistas.csv"
ARQUIVO_MANIFESTO = PASTA_TRATADOS / "manifesto_supabase.csv"

BUCKET_DADOS = "powerbi"
BUCKET_FOTOS = "artistas"

EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def carregar_configuracao():
    load_dotenv(PASTA_PROJETO / ".env")
    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    chave = os.getenv("SUPABASE_SECRET_KEY", "").strip()

    if not url:
        raise RuntimeError("SUPABASE_URL não encontrada no arquivo .env.")
    if not chave:
        raise RuntimeError("SUPABASE_SECRET_KEY não encontrada no arquivo .env.")

    return url, chave


def nome_bucket(bucket):
    if isinstance(bucket, dict):
        return str(bucket.get("name") or bucket.get("id") or "")
    return str(getattr(bucket, "name", "") or getattr(bucket, "id", ""))


def garantir_bucket(cliente: Client, nome: str):
    existentes = {nome_bucket(bucket) for bucket in cliente.storage.list_buckets()}

    if nome in existentes:
        print(f"Bucket '{nome}': existente")
        return

    cliente.storage.create_bucket(nome, options={"public": True})
    print(f"Bucket '{nome}': criado como público")


def url_publica(supabase_url: str, bucket: str, caminho_remoto: str):
    caminho_codificado = "/".join(
        quote(parte, safe="") for parte in caminho_remoto.split("/")
    )
    return (
        f"{supabase_url}/storage/v1/object/public/"
        f"{bucket}/{caminho_codificado}"
    )


def tipo_conteudo(caminho: Path):
    if caminho.suffix.lower() == ".csv":
        return "text/csv; charset=utf-8"
    return mimetypes.guess_type(caminho.name)[0] or "application/octet-stream"


def enviar_arquivo(
    supabase_url: str,
    chave: str,
    bucket: str,
    caminho_local: Path,
    caminho_remoto: str,
):
    caminho_codificado = "/".join(
        quote(parte, safe="") for parte in caminho_remoto.split("/")
    )
    endpoint = (
        f"{supabase_url}/storage/v1/object/"
        f"{bucket}/{caminho_codificado}"
    )
    cabecalhos = {
        "apikey": chave,
        "Authorization": f"Bearer {chave}",
        "Content-Type": tipo_conteudo(caminho_local),
        "Cache-Control": "3600",
        "x-upsert": "true",
    }

    ultimo_erro = None

    for tentativa in range(1, 5):
        try:
            with caminho_local.open("rb") as arquivo:
                resposta = requests.post(
                    endpoint,
                    headers=cabecalhos,
                    data=arquivo,
                    timeout=(30, 180),
                )

            if resposta.status_code not in {200, 201}:
                detalhe = resposta.text[:500]
                raise RuntimeError(
                    f"Supabase retornou HTTP {resposta.status_code}: {detalhe}"
                )

            return url_publica(supabase_url, bucket, caminho_remoto)

        except (requests.RequestException, RuntimeError) as erro:
            ultimo_erro = erro

            if tentativa == 4:
                break

            espera = 5 * tentativa
            print(
                f"      Tentativa {tentativa} falhou: {erro}\n"
                f"      Nova tentativa em {espera}s..."
            )
            time.sleep(espera)

    raise RuntimeError(
        f"Não foi possível enviar {caminho_local.name} após 4 tentativas: "
        f"{ultimo_erro}"
    )


def localizar_foto(caminho_registrado):
    texto = str(caminho_registrado or "").strip()
    if not texto or texto.lower() == "nan":
        return None

    caminho = Path(texto.replace("\\", "/"))
    if caminho.is_absolute():
        return caminho if caminho.exists() else None

    caminho_projeto = PASTA_PROJETO / caminho
    return caminho_projeto if caminho_projeto.exists() else None


def sincronizar_fotos(cliente: Client, supabase_url: str, chave: str):
    if not ARQUIVO_ARTISTAS.exists():
        raise FileNotFoundError(f"Cadastro não encontrado: {ARQUIVO_ARTISTAS}")

    artistas = pd.read_csv(
        ARQUIVO_ARTISTAS,
        encoding="utf-8-sig",
        dtype=str,
        keep_default_na=False,
    )

    if "foto_arquivo_local" not in artistas.columns:
        raise ValueError("A coluna foto_arquivo_local não existe em artistas.csv.")

    if "foto_url_publica" not in artistas.columns:
        artistas["foto_url_publica"] = ""

    enviados = 0
    ausentes = []

    print("\nENVIANDO FOTOS DOS ARTISTAS")

    for indice, linha in artistas.iterrows():
        nome = linha.get("nome_artista", linha.get("artista_id", "artista"))
        foto = localizar_foto(linha.get("foto_arquivo_local", ""))

        if foto is None:
            ausentes.append(str(nome))
            print(f" - {nome}: arquivo não encontrado")
            continue

        nome_remoto = foto.name.lower().replace(" ", "_")
        url = enviar_arquivo(
            supabase_url=supabase_url,
            chave=chave,
            bucket=BUCKET_FOTOS,
            caminho_local=foto,
            caminho_remoto=nome_remoto,
        )
        artistas.at[indice, "foto_url_publica"] = url
        enviados += 1
        print(f" - {nome}: enviada")

    artistas.to_csv(
        ARQUIVO_ARTISTAS,
        index=False,
        encoding="utf-8-sig",
    )

    return enviados, ausentes


def arquivos_csv_para_enviar():
    arquivos = []

    if PASTA_TRATADOS.exists():
        for caminho in sorted(PASTA_TRATADOS.glob("*.csv")):
            if caminho.name != ARQUIVO_MANIFESTO.name:
                arquivos.append((caminho, f"tratados/{caminho.name}"))

    for nome in ["artistas.csv", "programacao.csv"]:
        caminho = PASTA_REFERENCIAS / nome
        if caminho.exists():
            arquivos.append((caminho, f"referencias/{caminho.name}"))

    for nome in ["diario_projeto.csv", "frescor_fontes.csv", "integridade_projeto.csv"]:
        caminho = PASTA_METODOLOGIA / nome
        if caminho.exists():
            arquivos.append((caminho, f"metodologia/{caminho.name}"))

    return arquivos


def sincronizar_dados(cliente: Client, supabase_url: str, chave: str):
    registros = []
    agora = datetime.now(FUSO_BRASIL).isoformat(timespec="seconds")
    arquivos = arquivos_csv_para_enviar()

    print("\nENVIANDO BASES PARA O POWER BI")

    for numero, (local, remoto) in enumerate(arquivos, start=1):
        try:
            url = enviar_arquivo(
                supabase_url=supabase_url,
                chave=chave,
                bucket=BUCKET_DADOS,
                caminho_local=local,
                caminho_remoto=remoto,
            )
            status = "enviado"
            erro = ""
            print(f"[{numero}/{len(arquivos)}] {local.name}: enviado")
        except Exception as excecao:
            url = ""
            status = "erro"
            erro = str(excecao)
            print(f"[{numero}/{len(arquivos)}] {local.name}: ERRO — {excecao}")

        registros.append(
            {
                "arquivo": local.name,
                "grupo": remoto.split("/", 1)[0],
                "caminho_local": str(local.relative_to(PASTA_PROJETO)).replace("\\", "/"),
                "caminho_supabase": remoto,
                "url_publica": url,
                "tamanho_bytes": local.stat().st_size,
                "status": status,
                "erro": erro,
                "sincronizado_em": agora,
            }
        )

    manifesto = pd.DataFrame(registros)
    manifesto.to_csv(
        ARQUIVO_MANIFESTO,
        index=False,
        encoding="utf-8-sig",
    )

    enviar_arquivo(
        supabase_url=supabase_url,
        chave=chave,
        bucket=BUCKET_DADOS,
        caminho_local=ARQUIVO_MANIFESTO,
        caminho_remoto=f"tratados/{ARQUIVO_MANIFESTO.name}",
    )

    return manifesto


def main():
    print("SINCRONIZANDO ROCK IN RIO 2026 COM O SUPABASE")

    supabase_url, chave = carregar_configuracao()
    cliente = create_client(supabase_url, chave)

    garantir_bucket(cliente, BUCKET_FOTOS)
    garantir_bucket(cliente, BUCKET_DADOS)

    fotos_enviadas, fotos_ausentes = sincronizar_fotos(
        cliente,
        supabase_url,
        chave,
    )

    manifesto = sincronizar_dados(cliente, supabase_url, chave)
    enviados = int((manifesto["status"] == "enviado").sum())
    erros = int((manifesto["status"] == "erro").sum())

    print("\nSINCRONIZAÇÃO CONCLUÍDA")
    print(f"Fotos enviadas: {fotos_enviadas}")
    print(f"Fotos ausentes: {len(fotos_ausentes)}")
    print(f"Arquivos de dados enviados: {enviados}")
    print(f"Arquivos de dados com erro: {erros}")
    print(f"Manifesto: {ARQUIVO_MANIFESTO}")

    if fotos_ausentes:
        print("\nFotos não encontradas:")
        for nome in fotos_ausentes:
            print(f" - {nome}")

    if erros:
        raise RuntimeError(
            "A sincronização terminou com erro em um ou mais arquivos. "
            "Consulte manifesto_supabase.csv."
        )


if __name__ == "__main__":
    main()
