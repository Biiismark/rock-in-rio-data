from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import json
import re
import time
import unicodedata

import pandas as pd
import requests
from bs4 import BeautifulSoup
from googlenewsdecoder import gnewsdecoder


FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")

DATA_INICIO_RIR = pd.Timestamp(
    "2025-09-18",
    tz="America/Sao_Paulo",
)

DATA_LANCAMENTO_ULTIMATE = pd.Timestamp(
    "2026-05-18",
    tz="America/Sao_Paulo",
)

CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_TRATADOS = PASTA_PROJETO / "dados" / "tratados"
PASTA_HTMLS = (
    PASTA_PROJETO
    / "dados"
    / "brutos"
    / "noticias_heineken_rir"
    / "paginas"
)

ARQUIVO_ORIGINAL = (
    PASTA_TRATADOS
    / "noticias_heineken_rir.csv"
)

ARQUIVO_VALIDADO = (
    PASTA_TRATADOS
    / "noticias_heineken_rir_validadas.csv"
)

ARQUIVO_DASHBOARD = (
    PASTA_TRATADOS
    / "noticias_heineken_rir_dashboard.csv"
)

ARQUIVO_AUDITORIA = (
    PASTA_TRATADOS
    / "auditoria_validacao_noticias.csv"
)

PASTA_HTMLS.mkdir(
    parents=True,
    exist_ok=True,
)


def limpar_texto(valor):
    if valor is None:
        return ""

    if isinstance(valor, dict):
        partes = [
            limpar_texto(item)
            for item in valor.values()
        ]
        valor = " ".join(
            item for item in partes if item
        )

    elif isinstance(valor, (list, tuple, set)):
        partes = [
            limpar_texto(item)
            for item in valor
        ]
        valor = " ".join(
            item for item in partes if item
        )

    else:
        try:
            ausente = pd.isna(valor)
            if bool(ausente):
                return ""
        except (TypeError, ValueError):
            # Objetos vetoriais/estruturados não devem
            # interromper a validação de uma notícia.
            pass

    texto = unicodedata.normalize(
        "NFKC",
        str(valor),
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


def normalizar_texto(valor):
    texto = limpar_texto(valor)

    texto = unicodedata.normalize(
        "NFKD",
        texto,
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = texto.lower()

    texto = re.sub(
        r"[^a-z0-9]+",
        " ",
        texto,
    )

    return re.sub(
        r"\s+",
        " ",
        texto,
    ).strip()


def contem_heineken(texto):
    return "heineken" in normalizar_texto(texto)


def contem_rock_in_rio(texto):
    texto = normalizar_texto(texto)

    return (
        "rock in rio" in texto
        or "cidade do rock" in texto
    )


def contem_2026(texto):
    return "2026" in normalizar_texto(texto)


def contem_ultimate(texto):
    texto = normalizar_texto(texto)

    return (
        "heineken ultimate" in texto
        or (
            "heineken" in texto
            and "ultimate" in texto
        )
    )


def contem_heineken_zero(texto):
    texto = normalizar_texto(texto)

    padroes = [
        "heineken 0 0",
        "heineken zero",
        "heineken sem alcool",
        "heineken sem alcool",
    ]

    return any(
        padrao in texto
        for padrao in padroes
    )


def data_publicacao(valor):
    data = pd.to_datetime(
        valor,
        errors="coerce",
        utc=True,
    )

    if pd.isna(data):
        return pd.NaT

    return data.tz_convert(
        "America/Sao_Paulo"
    )


def decodificar_url_google(url_google):
    try:
        resultado = gnewsdecoder(
            url_google,
            interval=1,
        )

        if resultado.get("status"):
            return (
                limpar_texto(
                    resultado.get("decoded_url")
                ),
                "decodificado",
                "",
            )

        return (
            "",
            "falha na decodificação",
            limpar_texto(
                resultado.get("message")
            ),
        )

    except Exception as erro:
        return (
            "",
            "erro na decodificação",
            str(erro),
        )


def percorrer_json(objeto):
    descricoes = []

    if isinstance(objeto, dict):
        for chave, valor in objeto.items():
            chave_normalizada = (
                normalizar_texto(chave)
            )

            if chave_normalizada in {
                "description",
                "abstract",
                "article description",
            }:
                if not isinstance(
                    valor,
                    (dict, list, tuple, set),
                ):
                    texto = limpar_texto(valor)

                    if texto:
                        descricoes.append(texto)

            descricoes.extend(
                percorrer_json(valor)
            )

    elif isinstance(objeto, list):
        for item in objeto:
            descricoes.extend(
                percorrer_json(item)
            )

    return descricoes


def descricao_json_ld(sopa):
    descricoes = []

    scripts = sopa.find_all(
        "script",
        attrs={
            "type": "application/ld+json"
        },
    )

    for script in scripts:
        conteudo = script.string

        if not conteudo:
            continue

        try:
            objeto = json.loads(conteudo)
            descricoes.extend(
                percorrer_json(objeto)
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            continue

    return descricoes


def paragrafo_editorial(sopa):
    seletores = [
        "article p",
        "main article p",
        "main p",
        ".article-content p",
        ".post-content p",
        ".entry-content p",
        ".materia p",
        ".content p",
    ]

    textos_ignorados = [
        "assine",
        "aceite os cookies",
        "política de privacidade",
        "politica de privacidade",
        "publicidade",
        "newsletter",
        "receba nossas notícias",
        "receba nossas noticias",
        "todos os direitos reservados",
    ]

    for seletor in seletores:
        for elemento in sopa.select(seletor):
            texto = limpar_texto(
                elemento.get_text(
                    " ",
                    strip=True,
                )
            )

            texto_normalizado = (
                normalizar_texto(texto)
            )

            if len(texto) < 80:
                continue

            if any(
                ignorado in texto_normalizado
                for ignorado
                in textos_ignorados
            ):
                continue

            return texto

    return ""


def escolher_lead(sopa):
    candidatos = []

    metadados = [
        (
            "og:description",
            sopa.find(
                "meta",
                attrs={
                    "property": "og:description"
                },
            ),
        ),
        (
            "meta description",
            sopa.find(
                "meta",
                attrs={
                    "name": "description"
                },
            ),
        ),
        (
            "twitter:description",
            sopa.find(
                "meta",
                attrs={
                    "name": "twitter:description"
                },
            ),
        ),
    ]

    for origem, elemento in metadados:
        if elemento is None:
            continue

        texto = limpar_texto(
            elemento.get("content")
        )

        if len(texto) >= 50:
            candidatos.append(
                (origem, texto)
            )

    for texto in descricao_json_ld(sopa):
        if len(texto) >= 50:
            candidatos.append(
                ("JSON-LD", texto)
            )

    primeiro_paragrafo = paragrafo_editorial(
        sopa
    )

    if primeiro_paragrafo:
        candidatos.append(
            (
                "primeiro parágrafo",
                primeiro_paragrafo,
            )
        )

    if not candidatos:
        return "", "não encontrado"

    origem, lead = candidatos[0]

    lead = limpar_texto(lead)

    if len(lead) > 800:
        lead = lead[:797].rstrip() + "..."

    return lead, origem


def baixar_pagina(
    url_final,
    noticia_id,
):
    try:
        resposta = requests.get(
            url_final,
            headers=CABECALHOS,
            timeout=30,
            allow_redirects=True,
        )

        status_http = resposta.status_code
        content_type = resposta.headers.get(
            "Content-Type",
            "",
        )

        if status_http >= 400:
            return {
                "status_acesso": (
                    f"HTTP {status_http}"
                ),
                "status_http": status_http,
                "url_final": resposta.url,
                "lead": "",
                "origem_lead": "",
                "arquivo_html": "",
                "erro_acesso": "",
            }

        if "html" not in content_type.lower():
            return {
                "status_acesso": (
                    "conteúdo não HTML"
                ),
                "status_http": status_http,
                "url_final": resposta.url,
                "lead": "",
                "origem_lead": "",
                "arquivo_html": "",
                "erro_acesso": "",
            }

        resposta.encoding = (
            resposta.apparent_encoding
            or resposta.encoding
            or "utf-8"
        )

        html = resposta.text

        arquivo_html = (
            PASTA_HTMLS
            / f"{noticia_id}.html"
        )

        arquivo_html.write_text(
            html,
            encoding="utf-8",
            errors="ignore",
        )

        sopa = BeautifulSoup(
            html,
            "lxml",
        )

        lead, origem_lead = escolher_lead(
            sopa
        )

        return {
            "status_acesso": "acessível",
            "status_http": status_http,
            "url_final": resposta.url,
            "lead": lead,
            "origem_lead": origem_lead,
            "arquivo_html": str(
                arquivo_html
            ),
            "erro_acesso": "",
        }

    except requests.RequestException as erro:
        return {
            "status_acesso": "erro de acesso",
            "status_http": "",
            "url_final": url_final,
            "lead": "",
            "origem_lead": "",
            "arquivo_html": "",
            "erro_acesso": str(erro),
        }

    except Exception as erro:
        return {
            "status_acesso": "erro de processamento",
            "status_http": "",
            "url_final": url_final,
            "lead": "",
            "origem_lead": "",
            "arquivo_html": "",
            "erro_acesso": (
                f"{type(erro).__name__}: {erro}"
            ),
        }


def classificar_noticia(
    titulo,
    lead,
    data,
):
    texto_titulo = limpar_texto(titulo)
    texto_completo = limpar_texto(
        f"{titulo} {lead}"
    )

    rir_titulo = (
        contem_heineken(texto_titulo)
        and contem_rock_in_rio(texto_titulo)
        and contem_2026(texto_titulo)
    )

    rir_completo = (
        contem_heineken(texto_completo)
        and contem_rock_in_rio(texto_completo)
        and contem_2026(texto_completo)
    )

    ultimate_titulo = (
        contem_ultimate(texto_titulo)
    )

    ultimate_completo = (
        contem_ultimate(texto_completo)
    )

    zero_titulo = (
        contem_heineken_zero(texto_titulo)
    )

    zero_completo = (
        contem_heineken_zero(texto_completo)
    )

    no_periodo_rir = (
        not pd.isna(data)
        and data >= DATA_INICIO_RIR
    )

    no_periodo_ultimate = (
        not pd.isna(data)
        and data >= DATA_LANCAMENTO_ULTIMATE
    )

    categorias = []
    criterios = []

    if no_periodo_rir and rir_titulo:
        categorias.append(
            "Rock in Rio 2026"
        )
        criterios.append(
            "Rock in Rio confirmado pelo título"
        )

    elif no_periodo_rir and rir_completo:
        categorias.append(
            "Rock in Rio 2026"
        )
        criterios.append(
            "Rock in Rio confirmado pelo lead"
        )

    if (
        no_periodo_ultimate
        and ultimate_titulo
    ):
        categorias.append(
            "Heineken Ultimate"
        )
        criterios.append(
            "Ultimate confirmada pelo título"
        )

    elif (
        no_periodo_ultimate
        and ultimate_completo
    ):
        categorias.append(
            "Heineken Ultimate"
        )
        criterios.append(
            "Ultimate confirmada pelo lead"
        )

    if zero_titulo:
        categorias.append(
            "Heineken 0.0"
        )
        criterios.append(
            "Heineken 0.0 confirmada pelo título"
        )

    elif zero_completo:
        categorias.append(
            "Heineken 0.0"
        )
        criterios.append(
            "Heineken 0.0 confirmada pelo lead"
        )

    categorias = list(
        dict.fromkeys(categorias)
    )
    criterios = list(
        dict.fromkeys(criterios)
    )

    if categorias:
        return {
            "categoria_validada": (
                " + ".join(categorias)
            ),
            "status_validacao": "confirmada",
            "criterio_validacao": (
                " | ".join(criterios)
            ),
            "incluir_dashboard": True,
            "nivel_confianca": "alto",
        }

    menciona_algum_tema = any(
        [
            contem_heineken(texto_completo),
            contem_rock_in_rio(texto_completo),
            contem_ultimate(texto_completo),
        ]
    )

    if pd.isna(data):
        motivo = "Data de publicação ausente"

    elif data < DATA_INICIO_RIR:
        motivo = (
            "Publicação anterior ao ciclo "
            "do Rock in Rio 2026"
        )

    elif menciona_algum_tema and not lead:
        motivo = (
            "Título insuficiente e lead "
            "não recuperado"
        )

    elif menciona_algum_tema:
        motivo = (
            "Não confirmou simultaneamente "
            "marca, evento e edição"
        )

    else:
        motivo = (
            "Título e lead sem relação "
            "confirmada com o projeto"
        )

    if menciona_algum_tema and not lead:
        status = "pendente"
        confianca = "baixa"

    else:
        status = "irrelevante"
        confianca = "alto"

    return {
        "categoria_validada": "",
        "status_validacao": status,
        "criterio_validacao": motivo,
        "incluir_dashboard": False,
        "nivel_confianca": confianca,
    }


def salvar_parcial(registros):
    if not registros:
        return

    pd.DataFrame(registros).to_csv(
        ARQUIVO_VALIDADO,
        index=False,
        encoding="utf-8-sig",
    )


def carregar_cache():
    if not ARQUIVO_VALIDADO.exists():
        return {}

    cache = pd.read_csv(
        ARQUIVO_VALIDADO,
        encoding="utf-8-sig",
        dtype=str,
    )

    if (
        cache.empty
        or "noticia_id" not in cache.columns
    ):
        return {}

    return {
        str(linha["noticia_id"]): (
            linha.to_dict()
        )
        for _, linha in cache.iterrows()
    }


def main():
    print(
        "VALIDANDO NOTÍCIAS — "
        "HEINEKEN E ROCK IN RIO 2026"
    )

    if not ARQUIVO_ORIGINAL.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: "
            f"{ARQUIVO_ORIGINAL}"
        )

    noticias = pd.read_csv(
        ARQUIVO_ORIGINAL,
        encoding="utf-8-sig",
        dtype=str,
    ).fillna("")

    cache = carregar_cache()
    registros = []

    print(
        f"Notícias recebidas: {len(noticias)}"
    )
    print(
        f"Registros disponíveis no cache: "
        f"{len(cache)}"
    )
    print(
        f"Recorte Rock in Rio: "
        f"{DATA_INICIO_RIR.date()}"
    )
    print(
        f"Recorte Ultimate: "
        f"{DATA_LANCAMENTO_ULTIMATE.date()}"
    )

    for indice, (_, linha) in enumerate(
        noticias.iterrows(),
        start=1,
    ):
        noticia_id = linha["noticia_id"]
        titulo = linha["titulo"]

        print(
            f"\n[{indice}/{len(noticias)}] "
            f"{titulo[:90]}"
        )

        if noticia_id in cache:
            registro_cache = cache[
                noticia_id
            ]

            status_cache = limpar_texto(
                registro_cache.get(
                    "status_processamento"
                )
            )

            if status_cache == "concluído":
                registros.append(
                    registro_cache
                )

                print(
                    "   Reutilizada validação "
                    "anterior"
                )
                continue

        data = data_publicacao(
            linha["data_publicacao"]
        )

        if (
            not pd.isna(data)
            and data < DATA_INICIO_RIR
        ):
            acesso = {
                "status_acesso": (
                    "não acessada — fora do período"
                ),
                "status_http": "",
                "url_final": "",
                "lead": "",
                "origem_lead": "",
                "arquivo_html": "",
                "erro_acesso": "",
            }

            status_url = "não decodificada"
            erro_url = ""

        else:
            (
                url_final,
                status_url,
                erro_url,
            ) = decodificar_url_google(
                linha["link"]
            )

            if url_final:
                acesso = baixar_pagina(
                    url_final=url_final,
                    noticia_id=noticia_id,
                )

            else:
                acesso = {
                    "status_acesso": (
                        "URL original indisponível"
                    ),
                    "status_http": "",
                    "url_final": "",
                    "lead": "",
                    "origem_lead": "",
                    "arquivo_html": "",
                    "erro_acesso": erro_url,
                }

        classificacao = classificar_noticia(
            titulo=titulo,
            lead=acesso["lead"],
            data=data,
        )

        registro = linha.to_dict()

        registro.update(
            {
                "url_original_google": (
                    linha["link"]
                ),
                "url_final": (
                    acesso["url_final"]
                ),
                "status_decodificacao": (
                    status_url
                ),
                "erro_decodificacao": (
                    erro_url
                ),
                "status_acesso": (
                    acesso["status_acesso"]
                ),
                "status_http": (
                    acesso["status_http"]
                ),
                "lead_noticia": (
                    acesso["lead"]
                ),
                "origem_lead": (
                    acesso["origem_lead"]
                ),
                "arquivo_html_pagina": (
                    acesso["arquivo_html"]
                ),
                "erro_acesso": (
                    acesso["erro_acesso"]
                ),
                "categoria_validada": (
                    classificacao[
                        "categoria_validada"
                    ]
                ),
                "status_validacao": (
                    classificacao[
                        "status_validacao"
                    ]
                ),
                "criterio_validacao": (
                    classificacao[
                        "criterio_validacao"
                    ]
                ),
                "incluir_dashboard": (
                    classificacao[
                        "incluir_dashboard"
                    ]
                ),
                "nivel_confianca": (
                    classificacao[
                        "nivel_confianca"
                    ]
                ),
                "status_processamento": (
                    "concluído"
                ),
                "validado_em": (
                    datetime.now(
                        FUSO_BRASIL
                    ).isoformat(
                        timespec="seconds"
                    )
                ),
            }
        )

        registros.append(registro)

        print(
            f"   URL: {status_url} | "
            f"Acesso: {acesso['status_acesso']}"
        )
        print(
            f"   Lead: "
            f"{acesso['origem_lead'] or 'ausente'}"
        )
        print(
            f"   Validação: "
            f"{classificacao['status_validacao']}"
        )

        if indice % 10 == 0:
            salvar_parcial(registros)
            print("   Progresso salvo")

        time.sleep(1)

    salvar_parcial(registros)

    resultado = pd.DataFrame(registros)

    mascara_dashboard = (
        resultado["incluir_dashboard"]
        .astype(str)
        .str.lower()
        .eq("true")
    )

    dashboard = (
        resultado[
            mascara_dashboard
        ]
        .copy()
    )

    dashboard["data_ordem"] = pd.to_datetime(
        dashboard["data_publicacao"],
        errors="coerce",
        utc=True,
    )

    dashboard = (
        dashboard
        .sort_values(
            "data_ordem",
            ascending=False,
        )
        .drop(
            columns=["data_ordem"]
        )
        .reset_index(drop=True)
    )

    dashboard.to_csv(
        ARQUIVO_DASHBOARD,
        index=False,
        encoding="utf-8-sig",
    )

    auditoria = (
        resultado
        .groupby(
            [
                "status_acesso",
                "status_validacao",
                "categoria_validada",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            quantidade_noticias=(
                "noticia_id",
                "nunique",
            )
        )
        .sort_values(
            "quantidade_noticias",
            ascending=False,
        )
    )

    auditoria.to_csv(
        ARQUIVO_AUDITORIA,
        index=False,
        encoding="utf-8-sig",
    )

    confirmadas = (
        resultado["status_validacao"]
        .eq("confirmada")
        .sum()
    )

    pendentes = (
        resultado["status_validacao"]
        .eq("pendente")
        .sum()
    )

    irrelevantes = (
        resultado["status_validacao"]
        .eq("irrelevante")
        .sum()
    )

    leads = (
        resultado["lead_noticia"]
        .fillna("")
        .astype(str)
        .str.strip()
        .ne("")
        .sum()
    )

    urls_finais = (
        resultado["url_final"]
        .fillna("")
        .astype(str)
        .str.strip()
        .ne("")
        .sum()
    )

    print(
        "\nVALIDAÇÃO CONCLUÍDA"
    )
    print(
        f"Notícias processadas: "
        f"{len(resultado)}"
    )
    print(
        f"URLs originais recuperadas: "
        f"{urls_finais}"
    )
    print(
        f"Leads recuperados: {leads}"
    )
    print(
        f"Notícias confirmadas: "
        f"{confirmadas}"
    )
    print(
        f"Notícias pendentes: "
        f"{pendentes}"
    )
    print(
        f"Notícias irrelevantes: "
        f"{irrelevantes}"
    )
    print(
        f"Registros para o dashboard: "
        f"{len(dashboard)}"
    )

    print(
        f"\nBase validada: "
        f"{ARQUIVO_VALIDADO}"
    )
    print(
        f"Base do dashboard: "
        f"{ARQUIVO_DASHBOARD}"
    )
    print(
        f"Auditoria: "
        f"{ARQUIVO_AUDITORIA}"
    )
    print(
        f"HTMLs acessíveis: "
        f"{PASTA_HTMLS}"
    )

    print(
        "\nNOTA: páginas bloqueadas ou sem lead "
        "não foram confirmadas por suposição. "
        "Notícias explicitamente confirmadas pelo "
        "título podem entrar mesmo quando o veículo "
        "bloqueia a leitura automatizada."
    )


if __name__ == "__main__":
    main()