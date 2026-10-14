from pathlib import Path
import re

import pandas as pd


PASTA_PROJETO = Path(__file__).resolve().parents[1]
PASTA_METODOLOGIA = PASTA_PROJETO / "dados" / "metodologia"
ARQUIVO_CSV = PASTA_METODOLOGIA / "diario_projeto.csv"
ARQUIVO_MD = PASTA_METODOLOGIA / "diario_projeto.md"


def fase_oficial(data_registro: str) -> str:
    data = pd.Timestamp(data_registro)
    data_iso = data.date().isoformat()

    if data < pd.Timestamp("2026-09-03"):
        return "Pré-festival"
    if data_iso == "2026-09-03":
        return "Véspera do festival"
    if data_iso in {
        "2026-09-04", "2026-09-05", "2026-09-06", "2026-09-07",
        "2026-09-11", "2026-09-12", "2026-09-13",
    }:
        return "Dia de festival"
    if data_iso in {"2026-09-08", "2026-09-09", "2026-09-10"}:
        return "Intervalo entre os fins de semana do festival"
    if pd.Timestamp("2026-09-14") <= data <= pd.Timestamp("2026-09-20"):
        return "Pós-festival — primeiros 7 dias"
    if data > pd.Timestamp("2026-09-20"):
        return "Pós-festival"
    return "Pré-festival"


def corrigir_csv() -> int:
    if not ARQUIVO_CSV.exists():
        print("Diário CSV ainda não existe; nenhuma correção aplicada.")
        return 0

    diario = pd.read_csv(ARQUIVO_CSV, encoding="utf-8-sig", dtype={"data_registro": str})
    if diario.empty or "data_registro" not in diario.columns:
        return 0

    if "fase_monitoramento" not in diario.columns:
        diario["fase_monitoramento"] = ""

    fases_corretas = diario["data_registro"].map(fase_oficial)
    alteradas = int((diario["fase_monitoramento"].fillna("") != fases_corretas).sum())
    diario["fase_monitoramento"] = fases_corretas
    diario.to_csv(ARQUIVO_CSV, index=False, encoding="utf-8-sig")
    return alteradas


def corrigir_markdown() -> int:
    if not ARQUIVO_MD.exists():
        return 0

    texto = ARQUIVO_MD.read_text(encoding="utf-8")
    alteracoes = 0

    datas = pd.date_range("2026-09-08", "2026-09-10", freq="D")
    for data in datas:
        data_iso = data.date().isoformat()
        padrao = (
            rf"(## {re.escape(data_iso)}\n\n)"
            rf"- Fase do monitoramento: [^\n]*"
        )
        substituicao = (
            rf"\1- Fase do monitoramento: "
            "Intervalo entre os fins de semana do festival"
        )
        texto_novo, quantidade = re.subn(padrao, substituicao, texto)
        if quantidade:
            alteracoes += quantidade
            texto = texto_novo

    ARQUIVO_MD.write_text(texto, encoding="utf-8")
    return alteracoes


def main():
    PASTA_METODOLOGIA.mkdir(parents=True, exist_ok=True)
    csv_alteradas = corrigir_csv()
    md_alteradas = corrigir_markdown()
    print("FASES METODOLÓGICAS VERIFICADAS")
    print(f"Linhas CSV ajustadas: {csv_alteradas}")
    print(f"Blocos Markdown ajustados: {md_alteradas}")
    print("08–10/09 = Intervalo entre os fins de semana do festival")


if __name__ == "__main__":
    main()
