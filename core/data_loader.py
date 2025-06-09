# Em core/data_loader.py
import pandas as pd
from google.cloud import bigquery

# O ID da nossa tabela de resumo
TABELA_RESUMO_ID = "bblend-data-warehouse-dev.BI_CRM.RFV_ANALISE_HISTORICO"

def get_available_snapshots():
    """Busca apenas a lista de datas de snapshot disponíveis para popular os filtros."""
    try:
        client = bigquery.Client()
        query = f"SELECT DISTINCT data_snapshot FROM `{TABELA_RESUMO_ID}` ORDER BY data_snapshot DESC"
        df = client.query(query).to_dataframe()
        if 'data_snapshot' in df.columns:
            df['data_snapshot'] = pd.to_datetime(df['data_snapshot'])
        return df['data_snapshot'].tolist()
    except Exception as e:
        print(f"ERRO ao buscar snapshots disponíveis: {e}")
        return []

def get_data_for_snapshot(snapshot_date):
    """Busca os dados de RFV para UMA ÚNICA data de snapshot."""
    try:
        client = bigquery.Client()
        # Usamos parâmetros para evitar SQL Injection e garantir performance
        query = f"""
            SELECT * FROM `{TABELA_RESUMO_ID}`
            WHERE data_snapshot = @snapshot_date
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("snapshot_date", "DATE", snapshot_date.date()),
            ]
        )
        df = client.query(query, job_config=job_config).to_dataframe()
        print(f"Dados carregados para o snapshot {snapshot_date.date()}: {len(df)} linhas.")
        return df
    except Exception as e:
        print(f"ERRO ao buscar dados para o snapshot {snapshot_date.date()}: {e}")
        return None