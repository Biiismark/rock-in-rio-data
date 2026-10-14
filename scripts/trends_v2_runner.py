# -*- coding: utf-8 -*-
"""Runner de compatibilidade do pipeline Google Trends V2.

Normaliza strings vazias como NULL antes de gravar no Postgres/Supabase,
sem alterar os CSVs nem a lógica de coleta. Aceita os mesmos argumentos do
trends_v2_pipeline.py, como --baseline-only e --regions-only.
"""
import trends_v2_pipeline as pipeline

_clean_original = pipeline.clean


def clean_postgres(value):
    if isinstance(value, str) and not value.strip():
        return None
    return _clean_original(value)


pipeline.clean = clean_postgres

if __name__ == "__main__":
    pipeline.main()
