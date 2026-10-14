from datetime import datetime
from hashlib import sha1
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo
import re
import time
import unicodedata
import xml.etree.ElementTree as ET

import pandas as pd
import requests


CONSULTAS = [
    ('"Heineken" "Rock in Rio"', "Rock in Rio"),
    ('"Heineken" "Rock in Rio 2026"', "Rock in Rio"),
    ('"Heineken" patrocínio festival', "Patrocínio"),
    ('"Heineken" ativação "Rock in Rio"', "Ativações"),
    ('"Heineken" sustentabilidade festival', "Sustentabilidade"),
    ('"Heineken 0.0" "Rock in Rio"', "Heineken 0.0"),
    ('"Heineken Ultimate"', "Heineken Ultimate"),
    ('"Heineken Ultimate" Brasil', "Heineken Ultimate"),
    ('"Heineken Ultimate" lançamento', "Heineken Ultimate"),
    ('"Heineken Ultimate" "Rock in Rio"', "Heineken Ultimate"),
    ('"Heineken Ultimate" festival', "Heineken Ultimate"),
    ('"Heineken Ultimate" cerveja', "Heineken Ultimate"),
    ('"Heineken Ultimate" "low carb"', "Heineken Ultimate"),
    ('"Heineken Ultimate" calorias', "Heineken Ultimate"),
]

CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
}

FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")

PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_BRUTOS = (
    PASTA_PROJETO
    / "dados"
    / "brutos"
    / "noticias_heineken_rir"
    / "rss"
)
PASTA_TRATADOS = PASTA_PROJETO / "dados" / "tratados"

ARQUIVO_NOTICIAS = (
    PASTA_TRATADOS
    / "noticias_heineken_rir.csv"
)
ARQUIVO_RESUMO = (
    PASTA_TRATADOS
    / "noticias_heineken_rir_resumo.csv"
)
ARQUIVO_TERMOS = (
    PASTA_TRATADOS
    / "noticias_heineken_rir_termos.csv"
)
ARQUIVO_AUDITORIA = (
    PASTA_TRATADOS
    / "noticias_heineken_rir_auditoria.csv"
)

PASTA_BRUTOS.mkdir(parents=True, exist_ok=True)
PASTA_TRATADOS.mkdir(parents=True, exist_ok=True)

PALAVRAS_IGNORADAS = {
    "a", "ao", "aos", "as", "com", "como", "da", "das",
    "de", "do", "dos", "e", "em", "entre", "foi", "na",
    "nas", "no", "nos", "o", "os", "para", "por", "que",
    "se", "sem", "sobre", "sua", "suas", "um", "uma",
    "brasil", "brasileiro", "brasileira", "heineken",
    "rock", "rio", "noticia", "noticias",
}


def limpar_texto(valor):
    if valor is None or pd.isna(valor):
        return ""

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


def criar_id_noticia(titulo, veiculo):
    base = "|".join(
        [
            normalizar_texto(titulo),
            normalizar_texto(veiculo),
        ]
    )

    return sha1(
        base.encode("utf-8")
    ).hexdigest()[:20]


def criar_slug(texto):
    return normalizar_texto(
        texto
    ).replace(" ", "_")[:70]


def definir_janela():
    if ARQUIVO_NOTICIAS.exists():
        return "7d", "Atualização incremental"

    return "1y", "Carga histórica inicial"


def criar_url_rss(termo, janela):
    consulta = quote_plus(
        f"{termo} when:{janela}"
    )

    return (
        "https://news.google.com/rss/search"
        f"?q={consulta}"
        "&hl=pt-BR"
        "&gl=BR"
        "&ceid=BR:pt-419"
    )


def converter_data_publicacao(valor):
    data = pd.to_datetime(
        valor,
        errors="coerce",
        utc=True,
    )

    if pd.isna(data):
        return ""

    return (
        data
        .tz_convert(FUSO_BRASIL)
        .isoformat()
    )


def separar_titulo_veiculo(
    titulo_completo,
    veiculo_xml,
):
    titulo_completo = limpar_texto(
        titulo_completo
    )
    veiculo_xml = limpar_texto(
        veiculo_xml
    )

    if veiculo_xml:
        sufixo = f" - {veiculo_xml}"

        if titulo_completo.endswith(sufixo):
            return (
                titulo_completo[
                    :-len(sufixo)
                ].strip(),
                veiculo_xml,
            )

    if " - " in titulo_completo:
        titulo, veiculo = (
            titulo_completo.rsplit(
                " - ",
                1,
            )
        )

        return (
            limpar_texto(titulo),
            limpar_texto(veiculo),
        )

    return titulo_completo, veiculo_xml


def classificar_assunto_preliminar(titulo):
    texto = normalizar_texto(titulo)

    regras = [
        (
            "Heineken Ultimate",
            ["ultimate"],
        ),
        (
            "Heineken 0.0",
            [
                "heineken 0 0",
                "heineken zero",
                "sem alcool",
            ],
        ),
        (
            "Rock in Rio",
            [
                "rock in rio",
                "cidade do rock",
            ],
        ),
        (
            "Sustentabilidade",
            [
                "sustentabilidade",
                "sustentavel",
                "reciclagem",
                "energia renovavel",
            ],
        ),
        (
            "Ativações",
            [
                "ativacao",
                "experiencia",
                "smartband",
                "pulseira",
                "campanha",
            ],
        ),
        (
            "Patrocínio",
            [
                "patrocinio",
                "patrocinadora",
                "parceria",
            ],
        ),
    ]

    for assunto, palavras in regras:
        if any(
            palavra in texto
            for palavra in palavras
        ):
            return assunto

    return "A validar"


def relacao_preliminar(titulo):
    texto = normalizar_texto(titulo)

    if (
        "heineken" in texto
        and (
            "rock in rio" in texto
            or "cidade do rock" in texto
        )
        and "2026" in texto
    ):
        return "Confirmável pelo título"

    return "A validar pelo título ou lead"


def baixar_rss(termo, janela):
    url = criar_url_rss(
        termo,
        janela,
    )

    resposta = requests.get(
        url,
        headers=CABECALHOS,
        timeout=40,
    )

    resposta.raise_for_status()

    return (
        resposta.content,
        url,
        resposta.status_code,
    )


def preservar_rss(
    conteudo,
    termo,
    momento_arquivo,
):
    slug = criar_slug(termo)

    arquivo = (
        PASTA_BRUTOS
        / f"{momento_arquivo}_{slug}.xml"
    )

    arquivo.write_bytes(conteudo)

    return arquivo


def extrair_itens(
    conteudo,
    termo,
    categoria,
    data_coleta,
    coletado_em,
    url_rss,
):
    raiz = ET.fromstring(conteudo)
    itens = raiz.findall("./channel/item")
    registros = []

    for item in itens:
        titulo_completo = limpar_texto(
            item.findtext("title")
        )
        link = limpar_texto(
            item.findtext("link")
        )
        data_original = limpar_texto(
            item.findtext("pubDate")
        )

        fonte_elemento = item.find("source")

        veiculo_xml = (
            limpar_texto(fonte_elemento.text)
            if fonte_elemento is not None
            else ""
        )

        titulo, veiculo = separar_titulo_veiculo(
            titulo_completo,
            veiculo_xml,
        )

        if not titulo:
            continue

        registros.append(
            {
                "noticia_id": criar_id_noticia(
                    titulo,
                    veiculo,
                ),
                "titulo": titulo,
                "titulo_normalizado": (
                    normalizar_texto(titulo)
                ),
                "veiculo": veiculo,
                "data_publicacao": (
                    converter_data_publicacao(
                        data_original
                    )
                ),
                "data_publicacao_original": (
                    data_original
                ),
                "link": link,
                "termo_consultado": termo,
                "categoria_consulta": categoria,
                "assunto": (
                    classificar_assunto_preliminar(
                        titulo
                    )
                ),
                "relacao_rock_in_rio": (
                    relacao_preliminar(titulo)
                ),
                "data_coleta": data_coleta,
                "coletado_em": coletado_em,
                "url_rss": url_rss,
            }
        )

    return pd.DataFrame(registros)


def consolidar_resultados_da_execucao(dados):
    if dados.empty:
        return dados

    registros = []

    for _, grupo in dados.groupby(
        "noticia_id",
        sort=False,
    ):
        registro = grupo.iloc[0].to_dict()

        termos = sorted(
            {
                limpar_texto(valor)
                for valor
                in grupo["termo_consultado"]
                if limpar_texto(valor)
            }
        )

        categorias = sorted(
            {
                limpar_texto(valor)
                for valor
                in grupo["categoria_consulta"]
                if limpar_texto(valor)
            }
        )

        registro["termo_consultado"] = (
            " | ".join(termos)
        )
        registro["categoria_consulta"] = (
            " | ".join(categorias)
        )
        registro["quantidade_consultas"] = (
            len(termos)
        )

        registros.append(registro)

    return pd.DataFrame(registros)


def preparar_historico_anterior(historico):
    historico = historico.copy()

    if "primeira_coleta" not in historico.columns:
        historico["primeira_coleta"] = (
            historico.get(
                "data_coleta",
                "",
            )
        )

    if "ultima_coleta" not in historico.columns:
        historico["ultima_coleta"] = (
            historico.get(
                "data_coleta",
                "",
            )
        )

    if "quantidade_coletas" not in historico.columns:
        historico["quantidade_coletas"] = 1

    if "quantidade_consultas" not in historico.columns:
        historico["quantidade_consultas"] = 1

    historico["quantidade_coletas"] = (
        pd.to_numeric(
            historico["quantidade_coletas"],
            errors="coerce",
        )
        .fillna(1)
        .astype(int)
    )

    return historico


def atualizar_historico(
    novos_dados,
    data_coleta,
):
    novos_dados = consolidar_resultados_da_execucao(
        novos_dados
    )

    if ARQUIVO_NOTICIAS.exists():
        historico = pd.read_csv(
            ARQUIVO_NOTICIAS,
            encoding="utf-8-sig",
            dtype=str,
        ).fillna("")

        historico = preparar_historico_anterior(
            historico
        )

    else:
        historico = pd.DataFrame()

    ids_anteriores = set(
        historico.get(
            "noticia_id",
            pd.Series(dtype=str),
        ).astype(str)
    )

    ids_novos = set(
        novos_dados["noticia_id"]
        .astype(str)
    )

    ids_adicionados = (
        ids_novos - ids_anteriores
    )

    quantidade_ja_catalogada = len(
        ids_novos & ids_anteriores
    )

    if historico.empty:
        resultado = novos_dados.copy()

        resultado["primeira_coleta"] = (
            data_coleta
        )
        resultado["ultima_coleta"] = (
            data_coleta
        )
        resultado["quantidade_coletas"] = 1

    else:
        historico = historico.set_index(
            "noticia_id",
            drop=False,
        )

        novos_dados = novos_dados.set_index(
            "noticia_id",
            drop=False,
        )

        for noticia_id, linha in (
            novos_dados.iterrows()
        ):
            if noticia_id in historico.index:
                historico.at[
                    noticia_id,
                    "ultima_coleta",
                ] = data_coleta

                quantidade = pd.to_numeric(
                    historico.at[
                        noticia_id,
                        "quantidade_coletas",
                    ],
                    errors="coerce",
                )

                if pd.isna(quantidade):
                    quantidade = 1

                historico.at[
                    noticia_id,
                    "quantidade_coletas",
                ] = int(quantidade) + 1

            else:
                nova_linha = linha.to_dict()
                nova_linha["primeira_coleta"] = (
                    data_coleta
                )
                nova_linha["ultima_coleta"] = (
                    data_coleta
                )
                nova_linha["quantidade_coletas"] = 1

                historico.loc[
                    noticia_id
                ] = nova_linha

        resultado = historico.reset_index(
            drop=True
        )

    resultado["data_ordem"] = pd.to_datetime(
        resultado["data_publicacao"],
        errors="coerce",
        utc=True,
    )

    resultado = (
        resultado
        .sort_values(
            "data_ordem",
            ascending=False,
            na_position="last",
        )
        .drop(columns=["data_ordem"])
        .reset_index(drop=True)
    )

    resultado.to_csv(
        ARQUIVO_NOTICIAS,
        index=False,
        encoding="utf-8-sig",
    )

    adicionados = resultado[
        resultado["noticia_id"]
        .astype(str)
        .isin(ids_adicionados)
    ].copy()

    return (
        resultado,
        novos_dados.reset_index(
            drop=True
        ),
        adicionados,
        quantidade_ja_catalogada,
    )


def criar_resumo(historico):
    resumo = (
        historico
        .groupby(
            [
                "assunto",
                "relacao_rock_in_rio",
            ],
            as_index=False,
            dropna=False,
        )
        .agg(
            quantidade_publicacoes=(
                "noticia_id",
                "nunique",
            ),
            quantidade_veiculos=(
                "veiculo",
                "nunique",
            ),
            primeira_publicacao=(
                "data_publicacao",
                "min",
            ),
            ultima_publicacao=(
                "data_publicacao",
                "max",
            ),
        )
        .sort_values(
            "quantidade_publicacoes",
            ascending=False,
        )
    )

    resumo.to_csv(
        ARQUIVO_RESUMO,
        index=False,
        encoding="utf-8-sig",
    )


def criar_termos(historico):
    contagem = {}

    for titulo in historico["titulo"].fillna(""):
        palavras = normalizar_texto(
            titulo
        ).split()

        palavras = {
            palavra
            for palavra in palavras
            if (
                len(palavra) >= 4
                and palavra
                not in PALAVRAS_IGNORADAS
                and not palavra.isdigit()
            )
        }

        for palavra in palavras:
            contagem[palavra] = (
                contagem.get(palavra, 0) + 1
            )

    termos = pd.DataFrame(
        [
            {
                "termo": termo,
                "quantidade_publicacoes": quantidade,
            }
            for termo, quantidade
            in contagem.items()
        ]
    )

    if not termos.empty:
        termos = (
            termos
            .sort_values(
                [
                    "quantidade_publicacoes",
                    "termo",
                ],
                ascending=[
                    False,
                    True,
                ],
            )
            .head(100)
            .reset_index(drop=True)
        )

        termos.insert(
            0,
            "ranking_termo",
            termos.index + 1,
        )

    termos.to_csv(
        ARQUIVO_TERMOS,
        index=False,
        encoding="utf-8-sig",
    )


def main():
    agora = datetime.now(FUSO_BRASIL)

    data_coleta = agora.date().isoformat()
    coletado_em = agora.isoformat(
        timespec="seconds"
    )
    momento_arquivo = agora.strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    janela, tipo_execucao = definir_janela()

    print(
        "COLETANDO NOTÍCIAS — "
        "HEINEKEN E ROCK IN RIO 2026"
    )
    print(f"Modo: {tipo_execucao}")
    print(f"Janela consultada: {janela}")
    print(
        f"Consultas programadas: "
        f"{len(CONSULTAS)}"
    )

    todos_dados = []
    auditoria = []

    for indice, (
        termo,
        categoria,
    ) in enumerate(
        CONSULTAS,
        start=1,
    ):
        print(
            f"\n[{indice}/{len(CONSULTAS)}] "
            f"{termo}"
        )

        try:
            (
                conteudo,
                url_rss,
                status_http,
            ) = baixar_rss(
                termo,
                janela,
            )

            arquivo_bruto = preservar_rss(
                conteudo,
                termo,
                momento_arquivo,
            )

            dados = extrair_itens(
                conteudo=conteudo,
                termo=termo,
                categoria=categoria,
                data_coleta=data_coleta,
                coletado_em=coletado_em,
                url_rss=url_rss,
            )

            todos_dados.append(dados)

            auditoria.append(
                {
                    "data_coleta": data_coleta,
                    "coletado_em": coletado_em,
                    "janela": janela,
                    "termo_consultado": termo,
                    "categoria": categoria,
                    "status": "concluído",
                    "status_http": status_http,
                    "registros_extraidos": len(
                        dados
                    ),
                    "arquivo_bruto": str(
                        arquivo_bruto
                    ),
                    "erro": "",
                }
            )

            print(
                f"   Resultados: {len(dados)}"
            )

        except (
            requests.RequestException,
            ET.ParseError,
            ValueError,
        ) as erro:
            auditoria.append(
                {
                    "data_coleta": data_coleta,
                    "coletado_em": coletado_em,
                    "janela": janela,
                    "termo_consultado": termo,
                    "categoria": categoria,
                    "status": "erro",
                    "status_http": "",
                    "registros_extraidos": 0,
                    "arquivo_bruto": "",
                    "erro": str(erro),
                }
            )

            print(f"   ERRO: {erro}")

        if indice < len(CONSULTAS):
            time.sleep(2)

    auditoria_df = pd.DataFrame(
        auditoria
    )

    auditoria_df.to_csv(
        ARQUIVO_AUDITORIA,
        index=False,
        encoding="utf-8-sig",
    )

    if not todos_dados:
        raise RuntimeError(
            "Nenhuma consulta retornou dados."
        )

    brutos_execucao = pd.concat(
        todos_dados,
        ignore_index=True,
    )

    (
        historico,
        unicos_execucao,
        noticias_novas,
        ja_catalogadas,
    ) = atualizar_historico(
        brutos_execucao,
        data_coleta,
    )

    criar_resumo(historico)
    criar_termos(historico)

    erros = (
        auditoria_df["status"]
        .eq("erro")
        .sum()
    )

    print(
        "\nCOLETA DIÁRIA CONCLUÍDA"
    )
    print(
        f"Resultados brutos encontrados: "
        f"{len(brutos_execucao)}"
    )
    print(
        f"Publicações únicas na consulta: "
        f"{len(unicos_execucao)}"
    )
    print(
        f"Já catalogadas anteriormente: "
        f"{ja_catalogadas}"
    )
    print(
        f"Novas publicações adicionadas: "
        f"{len(noticias_novas)}"
    )
    print(
        f"Publicações acumuladas: "
        f"{len(historico)}"
    )
    print(
        f"Consultas com erro: {erros}"
    )

    if not noticias_novas.empty:
        print("\nNovas publicações:")

        for _, linha in (
            noticias_novas
            .sort_values(
                "data_publicacao",
                ascending=False,
            )
            .iterrows()
        ):
            print(
                f" - {linha['veiculo']}: "
                f"{linha['titulo']}"
            )

    print(
        f"\nHistórico: {ARQUIVO_NOTICIAS}"
    )
    print(
        f"Resumo: {ARQUIVO_RESUMO}"
    )
    print(
        f"Termos: {ARQUIVO_TERMOS}"
    )
    print(
        f"Auditoria: {ARQUIVO_AUDITORIA}"
    )
    print(
        f"RSS preservados em: "
        f"{PASTA_BRUTOS}"
    )

    print(
        "\nPRÓXIMA ETAPA: execute "
        "valida_noticias_heineken_rir.py. "
        "O cache fará com que somente as novas "
        "publicações precisem ser processadas."
    )


if __name__ == "__main__":
    main()