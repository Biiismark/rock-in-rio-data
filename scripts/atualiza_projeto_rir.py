from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import os
import subprocess
import sys
import time


FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")

PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_SCRIPTS = PASTA_PROJETO / "scripts"
PASTA_LOGS = PASTA_PROJETO / "logs"


# Ordem obrigatória da atualização diária.
# Cada cruzamento depende dos arquivos gerados nas etapas anteriores.
#
# Algumas fontes públicas podem bloquear coletas automatizadas de forma
# temporária. O Google Trends, em especial, pode retornar HTTP 429 quando
# há excesso de requisições. Nesse caso, a etapa deve registrar o problema,
# preservar os dados anteriores e permitir que notícias, TikTok, Supabase e
# histórico do GitHub continuem rodando normalmente.
ETAPAS = [
    {
        "nome": "Coleta do Spotify Brasil",
        "script": "coleta_spotify_kworb.py",
    },
    {
        "nome": "Coleta dos charts brasileiros",
        "script": "coleta_charts_brasil.py",
    },
    {
        "nome": "Cruzamento do Spotify com o festival",
        "script": "cruza_spotify_rir.py",
    },
    {
        "nome": "Cruzamento multiplataforma com o festival",
        "script": "cruza_charts_brasil_rir.py",
    },
    {
        "nome": "Coleta das páginas individuais do Kworb",
        "script": "coleta_paginas_individuais_kworb.py",
    },
    {
        "nome": "Extração brasileira das páginas individuais",
        "script": "extrai_paginas_individuais_brasil.py",
    },
    {
        "nome": "Consolidação da presença atual",
        "script": "consolida_presenca_atual_rir.py",
    },
    {
        "nome": "Criação das métricas finais",
        "script": "cria_metricas_presenca_rir.py",
    },
    {
        "nome": "Google Trends: evolução histórica (90 dias)",
        "script": "coleta_google_trends_rir.py",
        "argumentos": ["--somente-evolucao"],
        "fatal": False,
        "motivo_nao_fatal": "Google Trends pode limitar requisições. A série válida anterior é preservada.",
    },
    {
        "nome": "Google Trends: estados (últimos 7 dias)",
        "script": "coleta_google_trends_estados_7d.py",
        "fatal": False,
        "motivo_nao_fatal": (
            "Google Trends pode limitar requisições com erro 429. "
            "Quando isso ocorrer, os dados anteriores devem ser preservados "
            "e a atualização das demais fontes deve continuar."
        ),
    },
    {
        "nome": "Google Trends: consultas relacionadas (últimos 7 dias)",
        "script": "coleta_google_trends_consultas_relacionadas.py",
        "argumentos": ["--periodo", "7d", "--limite", "30"],
        "fatal": False,
        "motivo_nao_fatal": "A coleta é retomável, processada em lotes de duas entidades com pausas e preserva o último resultado válido.",
    },
    {
        "nome": "Coleta de notícias Heineken e Rock in Rio",
        "script": "coleta_noticias_heineken_rir.py",
    },
    {
        "nome": "Validação das notícias coletadas",
        "script": "valida_noticias_heineken_rir.py",
    },
    {
        "nome": "Preparação das notícias para o dashboard",
        "script": "prepara_noticias_dashboard.py",
    },
    {
        "nome": "Preparação do modelo temporal do Power BI",
        "script": "prepara_modelo_power_bi.py",
    },
    {
        "nome": "Registro do diário metodológico",
        "script": "registra_diario_projeto.py",
    },
]


def agora_brasil():
    return datetime.now(FUSO_BRASIL)


def formatar_duracao(segundos):
    segundos = int(round(segundos))
    minutos, segundos = divmod(segundos, 60)
    horas, minutos = divmod(minutos, 60)

    partes = []

    if horas:
        partes.append(f"{horas}h")

    if minutos:
        partes.append(f"{minutos}min")

    partes.append(f"{segundos}s")

    return " ".join(partes)


def validar_ambiente():
    scripts_ausentes = []

    for etapa in ETAPAS:
        caminho = PASTA_SCRIPTS / etapa["script"]

        if not caminho.exists():
            scripts_ausentes.append(str(caminho))

    if scripts_ausentes:
        mensagem = "\n".join(
            f" - {caminho}"
            for caminho in scripts_ausentes
        )

        raise FileNotFoundError(
            "Os seguintes scripts não foram encontrados:\n"
            f"{mensagem}"
        )


def etapa_eh_fatal(etapa):
    return bool(etapa.get("fatal", True))


def executar_etapa(numero, total, etapa, arquivo_log):
    caminho_script = PASTA_SCRIPTS / etapa["script"]
    fatal = etapa_eh_fatal(etapa)

    cabecalho = (
        f"\n{'=' * 72}\n"
        f"ETAPA {numero}/{total}: {etapa['nome']}\n"
        f"Script: {etapa['script']}\n"
        f"Obrigatória para interromper fluxo: {'sim' if fatal else 'não'}\n"
        f"Início: {agora_brasil().isoformat(timespec='seconds')}\n"
        f"{'=' * 72}\n"
    )

    print(cabecalho, end="", flush=True)
    arquivo_log.write(cabecalho)
    arquivo_log.flush()

    inicio = time.perf_counter()

    ambiente = os.environ.copy()
    ambiente["PYTHONUTF8"] = "1"

    processo = subprocess.Popen(
        [
            sys.executable,
            "-u",
            str(caminho_script),
            *etapa.get("argumentos", []),
        ],
        cwd=PASTA_PROJETO,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=ambiente,
    )

    if processo.stdout is None:
        raise RuntimeError(
            f"Não foi possível capturar a saída de {etapa['script']}."
        )

    for linha in processo.stdout:
        print(linha, end="", flush=True)
        arquivo_log.write(linha)
        arquivo_log.flush()

    codigo_saida = processo.wait()
    duracao = time.perf_counter() - inicio

    if codigo_saida != 0:
        resultado = (
            f"\nETAPA COM ERRO: {etapa['nome']}\n"
            f"Código de saída: {codigo_saida}\n"
            f"Duração: {formatar_duracao(duracao)}\n"
        )

        print(resultado, end="", flush=True)
        arquivo_log.write(resultado)
        arquivo_log.flush()

        if fatal:
            raise RuntimeError(
                f"A atualização parou na etapa {numero}: "
                f"{etapa['nome']}."
            )

        aviso = (
            "\nAVISO: etapa não fatal falhou, mas o fluxo continuará.\n"
            f"Motivo: {etapa.get('motivo_nao_fatal', 'falha tolerada nesta etapa.')}\n"
            "Os últimos dados válidos dessa fonte devem ser mantidos para o dashboard.\n"
        )

        print(aviso, end="", flush=True)
        arquivo_log.write(aviso)
        arquivo_log.flush()

        return {
            "numero": numero,
            "nome": etapa["nome"],
            "script": etapa["script"],
            "duracao": duracao,
            "status": "falhou_sem_interromper",
            "codigo_saida": codigo_saida,
        }

    resultado = (
        f"\nETAPA CONCLUÍDA: {etapa['nome']}\n"
        f"Duração: {formatar_duracao(duracao)}\n"
    )

    print(resultado, end="", flush=True)
    arquivo_log.write(resultado)
    arquivo_log.flush()

    return {
        "numero": numero,
        "nome": etapa["nome"],
        "script": etapa["script"],
        "duracao": duracao,
        "status": "concluída",
    }


def main():
    inicio_geral = time.perf_counter()
    inicio_em = agora_brasil()

    PASTA_LOGS.mkdir(parents=True, exist_ok=True)

    nome_log = (
        "atualizacao_rir_"
        + inicio_em.strftime("%Y-%m-%d_%H-%M-%S")
        + ".log"
    )

    caminho_log = PASTA_LOGS / nome_log

    print("ATUALIZAÇÃO COMPLETA DO PROJETO ROCK IN RIO 2026")
    print(
        "Interpretador Python: "
        f"{sys.executable}"
    )
    print(
        "Início: "
        f"{inicio_em.isoformat(timespec='seconds')}"
    )
    print(f"Etapas programadas: {len(ETAPAS)}")
    print(f"Log: {caminho_log}")

    resultados = []

    try:
        validar_ambiente()

        with caminho_log.open(
            "w",
            encoding="utf-8",
        ) as arquivo_log:
            arquivo_log.write(
                "ATUALIZAÇÃO COMPLETA DO PROJETO "
                "ROCK IN RIO 2026\n"
            )
            arquivo_log.write(
                f"Interpretador Python: {sys.executable}\n"
            )
            arquivo_log.write(
                "Início: "
                f"{inicio_em.isoformat(timespec='seconds')}\n"
            )
            arquivo_log.write(
                f"Etapas programadas: {len(ETAPAS)}\n"
            )
            arquivo_log.flush()

            for numero, etapa in enumerate(
                ETAPAS,
                start=1,
            ):
                resultado = executar_etapa(
                    numero=numero,
                    total=len(ETAPAS),
                    etapa=etapa,
                    arquivo_log=arquivo_log,
                )

                resultados.append(resultado)

            duracao_geral = (
                time.perf_counter() - inicio_geral
            )
            fim_em = agora_brasil()
            falhas_toleradas = [
                resultado for resultado in resultados
                if resultado.get("status") == "falhou_sem_interromper"
            ]

            resumo = (
                f"\n{'=' * 72}\n"
                "ATUALIZAÇÃO COMPLETA CONCLUÍDA\n"
                f"Etapas executadas: {len(resultados)}/{len(ETAPAS)}\n"
                f"Falhas toleradas: {len(falhas_toleradas)}\n"
                f"Duração total: {formatar_duracao(duracao_geral)}\n"
                f"Fim: {fim_em.isoformat(timespec='seconds')}\n"
                f"Log salvo em: {caminho_log}\n"
                f"{'=' * 72}\n"
            )

            if falhas_toleradas:
                resumo += "\nEtapas com falha tolerada:\n"
                for falha in falhas_toleradas:
                    resumo += (
                        f" - {falha['nome']} "
                        f"({falha['script']}) | código {falha['codigo_saida']}\n"
                    )

            print(resumo, end="", flush=True)
            arquivo_log.write(resumo)

    except (FileNotFoundError, RuntimeError) as erro:
        duracao_geral = time.perf_counter() - inicio_geral

        mensagem = (
            f"\nATUALIZAÇÃO INTERROMPIDA\n"
            f"Motivo: {erro}\n"
            f"Etapas executadas antes do erro: {len(resultados)}/{len(ETAPAS)}\n"
            f"Duração até o erro: "
            f"{formatar_duracao(duracao_geral)}\n"
            f"Consulte o log: {caminho_log}\n"
        )

        print(mensagem, end="", file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
