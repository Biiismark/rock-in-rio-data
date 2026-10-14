# -*- coding: utf-8 -*-
"""Executa a atualização geral sem as rotinas legadas do Google Trends.
O Google Trends V2 roda em job próprio, com controle de quota independente.
"""
import atualiza_projeto_rir as base

base.ETAPAS = [
    etapa for etapa in base.ETAPAS
    if not etapa.get("nome", "").startswith("Google Trends:")
]

# O arquivo validado mantém matérias contextuais para auditoria científica,
# mas a camada publicada no dashboard Heineken deve exigir foco editorial da marca.
for etapa in base.ETAPAS:
    if etapa.get("script") == "prepara_noticias_dashboard.py":
        etapa["script"] = "prepara_noticias_dashboard_marca.py"
        etapa["nome"] = "Preparação das notícias Heineken com foco editorial de marca"

if __name__ == "__main__":
    base.main()
