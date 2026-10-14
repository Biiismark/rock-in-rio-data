from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import json

import pandas as pd

FUSO = ZoneInfo("America/Sao_Paulo")
ROOT = Path(__file__).resolve().parents[1]
TRATADOS = ROOT / "dados" / "tratados"
REFERENCIAS = ROOT / "dados" / "referencias"
METODOLOGIA = ROOT / "dados" / "metodologia"
SAIDA = ROOT / "dados" / "relatorios_artigo"


def ler_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(path)


def fase(data_iso: str) -> str:
    d = pd.Timestamp(data_iso)
    if d < pd.Timestamp("2026-09-04"):
        return "Pré-festival"
    if data_iso in {"2026-09-04", "2026-09-05", "2026-09-06", "2026-09-07", "2026-09-11", "2026-09-12", "2026-09-13"}:
        return "Dia de festival"
    if data_iso in {"2026-09-08", "2026-09-09", "2026-09-10"}:
        return "Intervalo entre os fins de semana do festival"
    if pd.Timestamp("2026-09-14") <= d <= pd.Timestamp("2026-09-20"):
        return "Pós-festival - primeiros 7 dias"
    return "Pós-festival"


def ultimo_arquivo_horarios() -> Path | None:
    arquivos = sorted(METODOLOGIA.glob("programacao_horarios_auditados_*.csv"))
    return arquivos[-1] if arquivos else None


def fontes_estado() -> list[str]:
    controle = ler_csv(TRATADOS / "controle_atualizacao_fontes.csv")
    if controle.empty:
        return ["- Controle de atualização não disponível."]
    linhas = []
    for _, r in controle.iterrows():
        arquivo = str(r.get("arquivo", ""))
        grupo = str(r.get("grupo", ""))
        ultima = str(r.get("ultima_data", ""))
        atraso = r.get("atraso_dias", "")
        linhas.append(f"- {grupo or arquivo}: última referência `{ultima}` | lag `{atraso}` dia(s) | arquivo `{arquivo}`")
    return linhas


def shows_do_festival_day(data_iso: str) -> list[str]:
    prog = ler_csv(REFERENCIAS / "programacao.csv")
    if prog.empty:
        return ["- Programação indisponível."]
    hoje = prog[prog["data"].astype(str) == data_iso].copy()
    audit_path = ultimo_arquivo_horarios()
    audit = ler_csv(audit_path) if audit_path else pd.DataFrame()
    if not audit.empty and "apresentacao_id" in audit.columns:
        cols = [c for c in ["apresentacao_id", "data_hora_inicio_brt", "data_civil_inicio", "status_horario"] if c in audit.columns]
        hoje = hoje.merge(audit[cols].drop_duplicates("apresentacao_id"), on="apresentacao_id", how="left")
    if hoje.empty:
        return ["- Nenhuma apresentação do Palco Mundo neste festival day."]
    linhas = []
    for _, r in hoje.sort_values("horario").iterrows():
        ts = str(r.get("data_hora_inicio_brt", ""))
        civil = str(r.get("data_civil_inicio", ""))
        extra = f" | timestamp civil `{ts}`" if ts and ts != "nan" else ""
        if civil and civil != "nan" and civil != data_iso:
            extra += f" | **virada civil: {civil}**"
        linhas.append(f"- {r['nome_artista']} - horário de grade `{r.get('horario','')}`{extra}")
    return linhas


def tiktok_estado() -> str:
    path = TRATADOS / "tiktok" / "validacao_tiktok.json"
    if not path.exists():
        return "Validação TikTok local não disponível."
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return ", ".join(f"{k}={v}" for k, v in d.items())
    except Exception:
        return "Validação TikTok não pôde ser lida."


def main():
    agora = datetime.now(FUSO)
    data_iso = agora.date().isoformat()
    SAIDA.mkdir(parents=True, exist_ok=True)

    # IMPORTANTE: este arquivo é uma camada automática de dados/estado e não
    # substitui o relatório científico interpretativo, que pode ser revisado
    # manualmente e deve permanecer preservado no histórico.
    arquivo = SAIDA / f"{data_iso}_dados_auto.md"

    shows = "\n".join(shows_do_festival_day(data_iso))
    fontes = "\n".join(fontes_estado())
    tik = tiktok_estado()

    texto = f"""# Estado automático das fontes - {data_iso}\n\n**Status:** camada automática gerada após as coletas do dia; não contém interpretação científica final.\n\n**Fase:** {fase(data_iso)}  \n**Gerado em:** {agora.isoformat(timespec='seconds')}\n\n## 1. Apresentações do festival day\n\n{shows}\n\n> Atenção: a data do festival day não substitui o timestamp civil. Shows às 00:05 pertencem ao dia civil seguinte para análises intradiárias e de exposição.\n\n## 2. Estado automático das fontes\n\n{fontes}\n\n- TikTok local: {tik}\n\n## 3. Regras de leitura obrigatórias\n\n- D+1 civil não é automaticamente D+1 analítico.\n- Se a fonte ainda não publicou observação pós-show, registrar: **ainda sem observação pós-exposição disponível**.\n- Ausente, fora do ranking e zero são estados distintos.\n- Esta camada automática serve de insumo para o relatório científico do dia; ela não deve sobrescrever o arquivo interpretativo.\n\n## 4. Rastreabilidade\n\n- Data: {data_iso}\n- Horários auditados: `dados/metodologia/programacao_horarios_auditados_2026-09-04.csv`\n- Política de latência: `dados/metodologia/politica_latencia_fontes.csv`\n- Confundidores: `dados/metodologia/diario_confundidores.csv`\n- Template do relatório interpretativo: `dados/metodologia/template_relatorio_diario_festival.md`\n"""

    arquivo.write_text(texto, encoding="utf-8")
    print(f"Camada automática diária criada: {arquivo}")


if __name__ == "__main__":
    main()
