# -*- coding: utf-8 -*-
"""Google Trends V2 — pipeline diário do observatório Rock in Rio 2026.

A coleta é individual por entidade. O índice 0–100 é interpretado dentro da
trajetória da própria entidade; não é usado como volume absoluto entre artistas.
Os dois dias mais recentes ficam provisórios. A camada CSV publicada para o site
contém somente o corte comum consolidado. O banco também recebe linhas provisórias.

Modos:
  python scripts/trends_v2_pipeline.py
  python scripts/trends_v2_pipeline.py --baseline-only
  python scripts/trends_v2_pipeline.py --regions-only
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import math
import os
import random
import sys
import time

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client
from trendspy import Trends

FUSO = ZoneInfo("America/Sao_Paulo")
RAIZ = Path(__file__).resolve().parents[1]
TRATADOS = RAIZ / "dados" / "tratados"
TRATADOS.mkdir(parents=True, exist_ok=True)

GEO = "BR"
COLETA_ATE = date(2026, 9, 25)
MARGEM = int(os.getenv("TRENDS_V2_MARGEM_PROVISORIA_DIAS", "2"))
PAUSA_MIN = int(os.getenv("TRENDS_V2_PAUSA_MIN", "65"))
PAUSA_MAX = int(os.getenv("TRENDS_V2_PAUSA_MAX", "85"))
PAUSA_429 = int(os.getenv("TRENDS_V2_PAUSA_429", "300"))

EVOLUCAO = TRATADOS / "google_trends_v2_evolucao.csv"
RESUMO = TRATADOS / "google_trends_v2_resumo.csv"
ESTADOS = TRATADOS / "google_trends_v2_estados.csv"
BASELINE = TRATADOS / "google_trends_v2_baseline_2025.csv"
METADADOS = TRATADOS / "google_trends_v2_metadados.csv"
STATUS = TRATADOS / "google_trends_v2_status.csv"

# entidade, artista_id, nome exibido, tipo, data do show, MID/Topic, descrição
ENTIDADES = [
("Foo Fighters","art_foo_fighters","FOO FIGHTERS","artista","2026-09-04","/m/02r3zy","Banda"),
("Rise Against","art_rise_against","RISE AGAINST","artista","2026-09-04","/m/044cyx","Banda"),
("The Hives","art_the_hives","THE HIVES","artista","2026-09-04","/m/016p3r","Banda"),
("Nova Twins","art_nova_twins","NOVA TWINS","artista","2026-09-04","/g/11fm4j6mq9","Banda"),
("Avenged Sevenfold","art_avenged_sevenfold","AVENGED SEVENFOLD","artista","2026-09-05","/m/041f35","Banda"),
("Bring Me The Horizon","art_bring_me_the_horizon","BRING ME THE HORIZON","artista","2026-09-05","/m/0l030d","Banda"),
("mgk","art_mgk","mgk","artista","2026-09-05","/m/0gjcnwm","Rapper e cantor-compositor americano"),
("Sepultura","art_sepultura","SEPULTURA","artista","2026-09-05","/m/016lj_","Banda"),
("Calvin Harris","art_calvin_harris","CALVIN HARRIS","artista","2026-09-06","/m/0288c4g","DJ e produtor musical escocês"),
("Black Eyed Peas","art_black_eyed_peas","Black Eyed Peas","artista","2026-09-06","/m/01dwrc","Grupo musical"),
("Nelly","art_nelly","NELLY","artista","2026-09-06","/m/016pns","Rapper e cantor-compositor americano"),
("Barão Vermelho","art_barao_vermelho_encontro_formacao_original_convida_fernando_magalhaes","BARÃO VERMELHO – ENCONTRO FORMAÇÃO ORIGINAL convida Fernando Magalhães","artista","2026-09-06","/m/03zh89","Banda"),
("Elton John","art_elton_john","ELTON JOHN","artista","2026-09-07","/m/01vrz41","Pianista e cantor-compositor britânico"),
("Gilberto Gil","art_gilberto_gil","GILBERTO GIL","artista","2026-09-07","/m/01w632f","Cantor e ex-ministro da Cultura do Brasil"),
("Jon Batiste","art_jon_batiste","JON BATISTE","artista","2026-09-07","/m/0411jny","Cantor e compositor"),
("Luísa Sonza","art_luisa_sonza_convida_roberto_menescal","LUÍSA SONZA CONVIDA ROBERTO MENESCAL","artista","2026-09-07","/g/11fy_qdm4z","Cantora-compositora brasileira"),
("Stray Kids","art_stray_kids","STRAY KIDS","artista","2026-09-11","/g/11f3f_dy9l","Grupo de música pop"),
("Alok","art_alok_keep_art_human","ALOK – KEEP ART HUMAN","artista","2026-09-11","/g/11c5bsbjd9","DJ e produtor musical brasileiro"),
("Hwasa","art_hwasa","HWASA","artista","2026-09-11","/g/11b76jvk94","Rapper e cantora-compositora sul-coreana"),
("NEXZ","art_nexz","NEXZ","artista","2026-09-11","/g/11vm1m21nz","Banda"),
("Maroon 5","art_maroon_5","MAROON 5","artista","2026-09-12","/m/02k5sc","Banda"),
("Demi Lovato","art_demi_lovato","DEMI LOVATO","artista","2026-09-12","/m/02wb6yq","Artista musical"),
("J Balvin","art_j_balvin","J BALVIN","artista","2026-09-12","/m/0b__5gp","Cantor e compositor colombiano"),
("Pedro Sampaio","art_pedro_sampaio","PEDRO SAMPAIO","artista","2026-09-12","/g/11c53gms_b","DJ e cantor brasileiro"),
("Twenty One Pilots","art_twenty_one_pilots","TWENTY ONE PILOTS","artista","2026-09-13","/m/0sm28_4","Duo"),
("Halsey","art_halsey","HALSEY","artista","2026-09-13","/g/11b6gq6mkb","Cantora"),
("Lola Young","art_lola_young","LOLA YOUNG","artista","2026-09-13","/g/11gk3g8l1v","Cantora-compositora"),
("Ivete Sangalo","art_ivete_sangalo","IVETE SANGALO","artista","2026-09-13","/m/01ms3fy","Cantora e compositora brasileira"),
("Rock in Rio","evento_rock_in_rio","ROCK IN RIO","evento",None,"/m/04r7h6","Festival de música"),
("Heineken","marca_heineken","HEINEKEN","marca",None,"/m/013b0q","Cervejaria"),
]

UF = {"BR-AC":"Acre","BR-AL":"Alagoas","BR-AP":"Amapá","BR-AM":"Amazonas","BR-BA":"Bahia","BR-CE":"Ceará","BR-DF":"Distrito Federal","BR-ES":"Espírito Santo","BR-GO":"Goiás","BR-MA":"Maranhão","BR-MT":"Mato Grosso","BR-MS":"Mato Grosso do Sul","BR-MG":"Minas Gerais","BR-PA":"Pará","BR-PB":"Paraíba","BR-PR":"Paraná","BR-PE":"Pernambuco","BR-PI":"Piauí","BR-RJ":"Rio de Janeiro","BR-RN":"Rio Grande do Norte","BR-RS":"Rio Grande do Sul","BR-RO":"Rondônia","BR-RR":"Roraima","BR-SC":"Santa Catarina","BR-SP":"São Paulo","BR-SE":"Sergipe","BR-TO":"Tocantins"}


def agora(): return datetime.now(FUSO)

def meta_df():
    rows=[]
    for i,(ent,aid,nome,tipo,show,mid,descricao) in enumerate(ENTIDADES,1):
        rows.append({"artista_id":aid,"nome_artista":nome,"id":i,"entidade":ent,"tipo_entidade":tipo,"consulta_original":ent,"aliases":ent,"data_show":show or "","chave_google":mid,"titulo_google":ent,"tipo_topic_google":descricao,"modo_busca":"topic","status_2026":"OK","status_baseline_2025":"N/D" if ent=="Nova Twins" else "OK","data_validada_ate":"","biblioteca_principal":"trendspy","fallback":"trendspyg/trendspy validados em 2026-09-10","related_topics_status":"N/D - endpoint indisponível/quota","resolvido_em":agora().isoformat(timespec="seconds")})
    return pd.DataFrame(rows)


def config():
    load_dotenv(RAIZ/".env")
    url=os.getenv("SUPABASE_URL","").strip().rstrip("/")
    key=os.getenv("SUPABASE_SECRET_KEY","").strip()
    if not url or not key: raise RuntimeError("SUPABASE_URL/SUPABASE_SECRET_KEY ausentes.")
    return url,key


def clean(v):
    if v is None: return None
    if isinstance(v,float) and (math.isnan(v) or math.isinf(v)): return None
    if pd.isna(v): return None
    if hasattr(v,"item"):
        try: return v.item()
        except Exception: pass
    return v


def upsert(client,table,df,conflict,size=400):
    if df.empty: return
    rows=[{k:clean(v) for k,v in r.items()} for r in df.to_dict("records")]
    for i in range(0,len(rows),size): client.table(table).upsert(rows[i:i+size],on_conflict=conflict).execute()


def valor_col(df,mid):
    if mid in df.columns: return mid
    ign={"time [UTC]","isPartial","ispartial","geoName","geoCode"}
    cols=[c for c in df.columns if c not in ign]
    if not cols: raise ValueError("coluna de valor não encontrada")
    return cols[-1]


def quota(exc):
    s=f"{type(exc).__name__}: {exc}".lower()
    return any(x in s for x in ("429","quota exceeded","too many requests","trendsquotaexceedederror"))


def pause(a=None,b=None):
    s=random.randint(a or PAUSA_MIN,b or PAUSA_MAX); print(f"  pausa {s}s"); time.sleep(s)


def collect_time(tr,ent,mid,timeframe):
    for tentativa in range(2):
        try:
            df=tr.interest_over_time(mid,timeframe=timeframe,geo=GEO)
            if df is None or len(df)==0: return pd.DataFrame()
            if isinstance(df,pd.Series): df=df.to_frame()
            if not isinstance(df.index,pd.RangeIndex): df=df.reset_index()
            dc="time [UTC]" if "time [UTC]" in df.columns else df.columns[0]
            vc=valor_col(df,mid)
            return pd.DataFrame({"data":pd.to_datetime(df[dc],errors="coerce"),"interesse":pd.to_numeric(df[vc],errors="coerce")}).dropna()
        except Exception as exc:
            print(f"  erro {ent}: {type(exc).__name__}: {exc}")
            if quota(exc) and tentativa==0: time.sleep(PAUSA_429); continue
            return pd.DataFrame()
    return pd.DataFrame()


def seed_meta(client,meta):
    m=meta.copy().rename(columns={"id":"entidade_id"})
    cols=["artista_id","nome_artista","entidade","entidade_id","tipo_entidade","consulta_original","aliases","data_show","chave_google","titulo_google","tipo_topic_google","modo_busca","status_2026","status_baseline_2025","data_validada_ate","biblioteca_principal","fallback","related_topics_status","resolvido_em"]
    upsert(client,"trends_v2_entidades",m[cols],"artista_id")


def collect_baseline(client,meta,tr):
    parts=[]
    for i,r in meta.iterrows():
        if r.entidade=="Nova Twins":
            print(f"Baseline {i+1:02d}/30: Nova Twins = N/D documentado"); continue
        print(f"Baseline {i+1:02d}/30: {r.entidade}")
        d=collect_time(tr,r.entidade,r.chave_google,"2025-01-01 2025-12-31")
        if not d.empty:
            d["artista_id"]=r.artista_id; d["nome_artista"]=r.nome_artista; d["entidade"]=r.entidade; d["tipo_entidade"]=r.tipo_entidade; d["data_show"]=r.data_show; d["modo_busca"]=r.modo_busca; d["chave_google"]=r.chave_google; d["periodo"]="2025_baseline"; d["status_baseline"]="OK"; d["metodologia"]="V2 baseline semanal 2025 - consulta individual"; parts.append(d)
        if i<len(meta)-1: pause()
    if not parts: raise RuntimeError("baseline não retornou dados")
    out=pd.concat(parts,ignore_index=True); out["data"]=out.data.dt.strftime("%Y-%m-%d")
    out=out[["artista_id","nome_artista","entidade","tipo_entidade","data_show","data","interesse","modo_busca","chave_google","periodo","status_baseline","metodologia"]]
    out.to_csv(BASELINE,index=False,encoding="utf-8-sig")
    upsert(client,"trends_v2_baseline_2025",out,"artista_id,data")
    print("Baseline publicado:",len(out),"linhas")


def collect_regions(client,meta,tr,fim):
    parts=[]; tf=f"2026-01-01 {fim.isoformat()}"
    for i,r in meta.iterrows():
        print(f"Regiões {i+1:02d}/30: {r.entidade}")
        try:
            d=tr.interest_by_region(r.chave_google,timeframe=tf,geo=GEO,resolution="REGION",inc_low_vol=True)
            if d is not None and len(d):
                if isinstance(d,pd.Series): d=d.to_frame()
                if not isinstance(d.index,pd.RangeIndex): d=d.reset_index()
                vc=valor_col(d,r.chave_google); gc="geoCode" if "geoCode" in d.columns else None; gn="geoName" if "geoName" in d.columns else None
                x=pd.DataFrame({"artista_id":r.artista_id,"nome_artista":r.nome_artista,"entidade":r.entidade,"estado":d[gc].map(UF).fillna(d[gn] if gn else "") if gc else d[gn],"geo_code":d[gc] if gc else "","indice_estado_termo":pd.to_numeric(d[vc],errors="coerce"),"modo_busca":r.modo_busca,"data_validada_ate":(fim-timedelta(days=MARGEM)).isoformat(),"metodologia":"V2 individual por entidade"}).dropna(subset=["indice_estado_termo"]); parts.append(x)
        except Exception as exc:
            print("  região falhou:",type(exc).__name__,exc)
            if quota(exc): break
        if i<len(meta)-1: pause(20,35)
    if parts:
        out=pd.concat(parts,ignore_index=True); out.to_csv(ESTADOS,index=False,encoding="utf-8-sig"); upsert(client,"trends_v2_regioes",out,"artista_id,estado"); print("Regiões publicadas:",len(out))


def build_daily(client,meta,tr,fim):
    old=pd.read_csv(EVOLUCAO) if EVOLUCAO.exists() else pd.DataFrame()
    parts=[]; max_valid=[]; alvo=fim-timedelta(days=MARGEM); tf=f"2026-01-01 {fim.isoformat()}"
    for i,r in meta.iterrows():
        print(f"Série {i+1:02d}/30: {r.entidade}")
        d=collect_time(tr,r.entidade,r.chave_google,tf)
        if d.empty and not old.empty:
            d=old[old.artista_id.eq(r.artista_id)][["data","interesse"]].copy(); d["data"]=pd.to_datetime(d.data,errors="coerce")
            print("  preservando última série válida")
        if d.empty:
            print("  sem série válida para esta execução"); continue
        d=d.dropna().sort_values("data"); d["is_partial"]=d.data.dt.date>alvo
        valid=d[~d.is_partial].copy()
        if valid.empty: continue
        max_valid.append(valid.data.max().date())
        valid["percentil_intra_artista_2026"]=(valid.interesse.rank(method="average",pct=True)*100).round(2)
        mean=float(valid.interesse.mean()); med=float(valid.interesse.median()); std=float(valid.interesse.std(ddof=0))
        valid["zscore_intra_artista_2026"]=((valid.interesse-mean)/std).round(4) if std else 0.0
        p=d[d.is_partial].copy(); p["percentil_intra_artista_2026"]=None; p["zscore_intra_artista_2026"]=None
        g=pd.concat([valid,p],ignore_index=True); g["media_2026_intra"]=round(mean,4); g["mediana_2026_intra"]=round(med,4); g["artista_id"]=r.artista_id; g["nome_artista"]=r.nome_artista; g["entidade"]=r.entidade; g["tipo_entidade"]=r.tipo_entidade; g["data_show"]=r.data_show
        show=pd.to_datetime(r.data_show,errors="coerce"); g["d_relativo"]=(g.data-show).dt.days if pd.notna(show) else None; g["interesse_comparavel"]=g.interesse; g["modo_busca"]=r.modo_busca; g["chave_google"]=r.chave_google; g["periodo"]="2026_principal"; g["status_dado"]=g.is_partial.map(lambda v:"provisorio" if v else "consolidado"); g["metodologia"]="V2 individual por entidade"; parts.append(g)
        if i<len(meta)-1: pause()
    if not parts: raise RuntimeError("nenhuma série V2 disponível")
    common=min(max_valid); evo=pd.concat(parts,ignore_index=True); beyond=evo.data.dt.date>common; evo.loc[beyond,"is_partial"]=True; evo.loc[beyond,"status_dado"]="provisorio"; evo.loc[beyond,"percentil_intra_artista_2026"]=None; evo.loc[beyond,"zscore_intra_artista_2026"]=None; evo["data_validada_ate"]=common.isoformat(); evo["data"]=evo.data.dt.strftime("%Y-%m-%d")
    cols=["artista_id","nome_artista","tipo_entidade","entidade","data_show","data","d_relativo","interesse","interesse_comparavel","percentil_intra_artista_2026","zscore_intra_artista_2026","media_2026_intra","mediana_2026_intra","modo_busca","chave_google","periodo","is_partial","status_dado","data_validada_ate","metodologia"]
    evo=evo[cols]
    db=evo.rename(columns={"percentil_intra_artista_2026":"percentil_intra_artista","zscore_intra_artista_2026":"zscore_intra_artista"}).copy(); db=db.rename(columns={"is_partial":"is_partial"})
    client.table("trends_v2_interesse").delete().neq("artista_id","__never__").execute(); upsert(client,"trends_v2_interesse",db[["artista_id","nome_artista","entidade","tipo_entidade","data_show","data","d_relativo","interesse","percentil_intra_artista","zscore_intra_artista","media_2026_intra","mediana_2026_intra","modo_busca","chave_google","periodo","is_partial","status_dado","data_validada_ate","metodologia"]],"artista_id,data")
    consolidated=evo[evo.status_dado.eq("consolidado")].copy(); consolidated.to_csv(EVOLUCAO,index=False,encoding="utf-8-sig")
    rows=[]
    baseline_counts=pd.read_csv(BASELINE).groupby("artista_id").size().to_dict() if BASELINE.exists() else {}
    for _,r in meta.iterrows():
        g=consolidated[consolidated.artista_id.eq(r.artista_id)].sort_values("data")
        if g.empty: continue
        last=g.iloc[-1]; peak=g.interesse.max(); peakdate=g[g.interesse.eq(peak)].iloc[0].data; n25=int(baseline_counts.get(r.artista_id,0)); status25="N/D" if r.entidade=="Nova Twins" else ("OK" if n25 or r.status_baseline_2025=="OK" else "N/D")
        rows.append({"ranking_atencao_relativa":0,"ranking_interesse_busca":0,"artista_id":r.artista_id,"nome_artista":r.nome_artista,"termo":r.entidade,"tipo_entidade":r.tipo_entidade,"modo_busca":r.modo_busca,"chave_google":r.chave_google,"interesse_atual":last.interesse,"percentil_atual":last.percentil_intra_artista_2026,"zscore_atual":last.zscore_intra_artista_2026,"media_interesse":round(float(g.interesse.mean()),4),"mediana_2026":round(float(g.interesse.median()),4),"pico_interesse":peak,"data_pico":peakdate,"pontos_temporais":len(g),"n_2025":n25 if n25 else (0 if status25=="N/D" else 53),"status_baseline_2025":status25,"data_atual":last.data,"data_validada_ate":common.isoformat(),"status_dado":"consolidado","nota_metodologica":"Percentil atual é intra-entidade; índice 0–100 não compara volume absoluto entre entidades."})
    summary=pd.DataFrame(rows); summary["ranking_atencao_relativa"]=summary.percentil_atual.rank(method="min",ascending=False).astype(int); summary["ranking_interesse_busca"]=summary.ranking_atencao_relativa; summary=summary.sort_values(["ranking_atencao_relativa","nome_artista"]); summary.to_csv(RESUMO,index=False,encoding="utf-8-sig")
    sdb=summary.rename(columns={"termo":"entidade"})[["artista_id","nome_artista","entidade","tipo_entidade","modo_busca","chave_google","interesse_atual","percentil_atual","zscore_atual","media_interesse","mediana_2026","pico_interesse","data_pico","pontos_temporais","n_2025","status_baseline_2025","data_atual","data_validada_ate","status_dado","nota_metodologica"]]; upsert(client,"trends_v2_resumo",sdb,"artista_id")
    st=pd.DataFrame([{"versao":"V2","gerado_em":agora().date().isoformat(),"data_validada_ate":common.isoformat(),"entidades_2026":int(summary.artista_id.nunique()),"entidades_baseline_2025":29,"provisorio_disponivel_ate":fim.isoformat(),"related_topics":"N/D","regra_comparacao":"intra-artista","fonte":"Google Trends Brasil"}]); st.to_csv(STATUS,index=False,encoding="utf-8-sig"); upsert(client,"trends_v2_status",st,"versao")
    meta.loc[:,"data_validada_ate"]=common.isoformat(); meta.to_csv(METADADOS,index=False,encoding="utf-8-sig"); seed_meta(client,meta)
    print("Corte comum consolidado:",common,"| entidades:",summary.artista_id.nunique())
    return common


def main():
    print("GOOGLE TRENDS V2 —",agora().isoformat(timespec="seconds"))
    url,key=config(); client=create_client(url,key); meta=meta_df(); meta.to_csv(METADADOS,index=False,encoding="utf-8-sig"); seed_meta(client,meta); tr=Trends(); real=agora().date(); fim=min(real,COLETA_ATE)
    if "--baseline-only" in sys.argv:
        collect_baseline(client,meta,tr); return
    if "--regions-only" in sys.argv:
        collect_regions(client,meta,tr,fim); return
    if real>COLETA_ATE and EVOLUCAO.exists():
        print("Janela V2 congelada em",COLETA_ATE,"para preservar granularidade diária."); return
    build_daily(client,meta,tr,fim)
    if agora().weekday()==6 or not ESTADOS.exists(): collect_regions(client,meta,tr,fim)

if __name__=="__main__": main()
