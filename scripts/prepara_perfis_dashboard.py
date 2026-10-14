from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import re
import shutil

import pandas as pd


FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")

PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_REFERENCIAS = PASTA_PROJETO / "dados" / "referencias"

ARQUIVO_ARTISTAS = PASTA_REFERENCIAS / "artistas.csv"
ARQUIVO_AUDITORIA = (
    PASTA_REFERENCIAS / "auditoria_perfis_dashboard.csv"
)

# Chamadas promocionais do site. Elas permanecem na bio oficial integral,
# mas não entram no campo curto utilizado no dashboard.
PADROES_CHAMADA = [
    r"\b(?:no\s+)?dia\s+\d{1,2}\s*[.]?\s*set\b",
    r"\b(?:no\s+)?dia\s+\d{1,2}\b",
    r"\bprepare-se para\b",
    r"\bvocê vai poder\b",
    r"\bvocê vai ver\b",
    r"\bvolt[aá] à cidade do rock\b",
]


def limpar_espacos(texto):
    texto = str(texto or "")
    texto = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", texto)
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r" *\n *", "\n", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def corrigir_tipografia_oficial(artista_id, bio):
    # O HTML oficial do Foo Fighters contém “31º aniversário”. A coleta
    # anterior usou NFKC e transformou o indicador ordinal em letra “o”.
    if artista_id == "art_foo_fighters":
        bio = bio.replace("31o aniversário", "31º aniversário")

    return bio


def contem_chamada(texto):
    return any(
        re.search(padrao, texto, flags=re.IGNORECASE)
        for padrao in PADROES_CHAMADA
    )


def remover_chamada_dentro_paragrafo(paragrafo):
    # Algumas páginas juntam conteúdo biográfico e a chamada do show no mesmo
    # parágrafo. Conserva-se somente o trecho anterior à chamada explícita.
    marcadores = [
        r"\s+(?:No\s+)?Dia\s+\d{1,2}\s*[.]?\s*SET\b",
        r"\s+E\s+no\s+dia\s+\d{1,2}\s*[.]?\s*SET\b",
    ]

    resultado = paragrafo

    for marcador in marcadores:
        partes = re.split(
            marcador,
            resultado,
            maxsplit=1,
            flags=re.IGNORECASE,
        )
        resultado = partes[0].strip()

    return resultado


def criar_bio_dashboard(bio):
    paragrafos = [
        limpar_espacos(paragrafo)
        for paragrafo in re.split(r"\n\s*\n", bio)
        if limpar_espacos(paragrafo)
    ]

    substantivos = []
    removidos = []

    for paragrafo in paragrafos:
        sem_chamada = remover_chamada_dentro_paragrafo(paragrafo)

        if sem_chamada and sem_chamada != paragrafo:
            substantivos.append(sem_chamada)
            removidos.append(paragrafo[len(sem_chamada):].strip())
            continue

        if contem_chamada(paragrafo):
            removidos.append(paragrafo)
        else:
            substantivos.append(paragrafo)

    # Duas passagens oficiais mantêm a página legível em 1920 x 1080. O texto
    # integral continua preservado em bio_curta.
    selecionados = substantivos[:2]

    if not selecionados and paragrafos:
        selecionados = paragrafos[:1]

    return (
        "\n\n".join(selecionados),
        len(paragrafos),
        len(substantivos),
        len(removidos),
    )


def main():
    agora = datetime.now(FUSO_BRASIL)

    print("PREPARANDO PERFIS PARA O DASHBOARD")

    if not ARQUIVO_ARTISTAS.exists():
        raise FileNotFoundError(f"Cadastro não encontrado: {ARQUIVO_ARTISTAS}")

    artistas = pd.read_csv(
        ARQUIVO_ARTISTAS,
        encoding="utf-8-sig",
        dtype=str,
        keep_default_na=False,
    )

    obrigatorias = {
        "artista_id",
        "nome_artista",
        "bio_curta",
        "foto_arquivo_local",
    }
    ausentes = sorted(obrigatorias - set(artistas.columns))

    if ausentes:
        raise ValueError(
            "Colunas ausentes em artistas.csv: " + ", ".join(ausentes)
        )

    nome_backup = (
        "artistas_antes_perfis_dashboard_"
        + agora.strftime("%Y-%m-%d_%H-%M-%S")
        + ".csv"
    )
    arquivo_backup = PASTA_REFERENCIAS / nome_backup
    shutil.copy2(ARQUIVO_ARTISTAS, arquivo_backup)

    auditoria = []

    for indice, linha in artistas.iterrows():
        artista_id = linha["artista_id"].strip()
        nome = linha["nome_artista"].strip()
        bio_original_arquivo = limpar_espacos(linha["bio_curta"])
        bio_integral = corrigir_tipografia_oficial(
            artista_id,
            bio_original_arquivo,
        )

        (
            bio_dashboard,
            paragrafos_integrais,
            paragrafos_substantivos,
            chamadas_removidas,
        ) = criar_bio_dashboard(bio_integral)

        observacao = ""
        if artista_id == "art_pedro_sampaio":
            observacao = (
                "A bio oficial menciona Palco Sunset; a programação oficial "
                "cadastrada indica Palco Mundo. Data e palco devem vir de "
                "programacao.csv."
            )

        artistas.at[indice, "bio_curta"] = bio_integral
        artistas.at[indice, "bio_dashboard"] = bio_dashboard
        artistas.at[indice, "bio_dashboard_fonte"] = "Trechos da bio oficial do Rock in Rio"
        artistas.at[indice, "perfil_validado"] = "True"
        artistas.at[indice, "perfil_validado_em"] = agora.isoformat(timespec="seconds")
        artistas.at[indice, "perfil_observacao"] = observacao

        auditoria.append(
            {
                "validado_em": agora.isoformat(timespec="seconds"),
                "artista_id": artista_id,
                "nome_artista": nome,
                "caracteres_bio_integral": len(bio_integral),
                "caracteres_bio_dashboard": len(bio_dashboard),
                "paragrafos_integrais": paragrafos_integrais,
                "paragrafos_substantivos": paragrafos_substantivos,
                "paragrafos_dashboard": len(
                    re.split(r"\n\s*\n", bio_dashboard)
                ) if bio_dashboard else 0,
                "chamadas_promocionais_removidas": chamadas_removidas,
                "tipografia_corrigida": bio_integral != bio_original_arquivo,
                "foto_arquivo_local": linha["foto_arquivo_local"],
                "status": "validado",
                "observacao": observacao,
            }
        )

    auditoria_df = pd.DataFrame(auditoria)

    if artistas["bio_dashboard"].str.strip().eq("").any():
        nomes = artistas.loc[
            artistas["bio_dashboard"].str.strip().eq(""),
            "nome_artista",
        ].tolist()
        raise ValueError("Bio de dashboard vazia para: " + ", ".join(nomes))

    artistas.to_csv(ARQUIVO_ARTISTAS, index=False, encoding="utf-8-sig")
    auditoria_df.to_csv(ARQUIVO_AUDITORIA, index=False, encoding="utf-8-sig")

    print("\nPERFIS PREPARADOS")
    print(f"Artistas processados: {len(artistas)}")
    print(f"Perfis validados: {(artistas['perfil_validado'] == 'True').sum()}")
    print(
        "Bios com chamadas promocionais removidas: "
        f"{(auditoria_df['chamadas_promocionais_removidas'] > 0).sum()}"
    )
    print(
        "Correções tipográficas: "
        f"{auditoria_df['tipografia_corrigida'].sum()}"
    )
    print(
        "Tamanho das bios do dashboard: "
        f"{auditoria_df['caracteres_bio_dashboard'].min()} a "
        f"{auditoria_df['caracteres_bio_dashboard'].max()} caracteres"
    )
    print(f"\nCadastro atualizado: {ARQUIVO_ARTISTAS}")
    print(f"Backup anterior: {arquivo_backup}")
    print(f"Auditoria: {ARQUIVO_AUDITORIA}")
    print(
        "\nA bio oficial integral permanece em bio_curta. "
        "Use bio_dashboard na página do artista."
    )


if __name__ == "__main__":
    main()
