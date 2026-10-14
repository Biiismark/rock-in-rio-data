# -*- coding: utf-8 -*-
"""Prepara a página Heineken com foco editorial de marca.

A base validada continua preservando matérias contextuais para auditoria/pesquisa,
mas o dashboard só recebe publicações cujo título explicita Heineken ou uma
iniciativa proprietária monitorada. As menções contextuais são salvas em camada
separada para não perder informação científica.
"""
import unicodedata

import prepara_noticias_dashboard as base


TERMOS_FOCO_MARCA = (
    "heineken",
    "the loudest playlist",
    "green your city",
    "hei app",
    "heineken ultimate",
)

ARQUIVO_CONTEXTUAIS = base.PASTA_TRATADOS / "noticias_heineken_rir_contextuais.csv"


def normalizar(valor):
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.lower().split())


def foco_editorial_heineken(titulo):
    texto = normalizar(titulo)
    return any(termo in texto for termo in TERMOS_FOCO_MARCA)


_preparar_publicacoes_original = base.preparar_publicacoes


def preparar_publicacoes_marca():
    publicacoes = _preparar_publicacoes_original()
    if publicacoes.empty:
        publicacoes.to_csv(ARQUIVO_CONTEXTUAIS, index=False, encoding="utf-8-sig")
        return publicacoes

    mascara = publicacoes["titulo"].map(foco_editorial_heineken)
    contextuais = publicacoes[~mascara].copy()
    filtradas = publicacoes[mascara].copy()

    contextuais["camada_editorial"] = "mencao_contextual"
    contextuais["motivo_exclusao_dashboard"] = (
        "marca/iniciativa proprietaria nao explicitada no titulo"
    )
    contextuais.to_csv(ARQUIVO_CONTEXTUAIS, index=False, encoding="utf-8-sig")

    print(
        "Filtro editorial Heineken: "
        f"{len(filtradas)} publicações com foco de marca; "
        f"{len(contextuais)} menções contextuais preservadas em camada separada."
    )
    print(f"Menções contextuais: {ARQUIVO_CONTEXTUAIS}")
    return filtradas


base.preparar_publicacoes = preparar_publicacoes_marca


if __name__ == "__main__":
    base.main()
