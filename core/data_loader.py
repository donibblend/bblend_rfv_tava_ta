# Em core/data_loader.py (VERSÃO DE DEPURAÇÃO)
import pandas as pd
from google.cloud import bigquery

TABELA_RESUMO_ID = "bblend-data-warehouse-dev.BI_CRM.RFV_ANALISE_HISTORICO"

def get_available_snapshots():
    try:
        client = bigquery.Client()
        query = f"SELECT DISTINCT data_snapshot FROM `{TABELA_RESUMO_ID}` ORDER BY data_snapshot DESC"
        df = client.query(query).to_dataframe()
        return pd.to_datetime(df['data_snapshot']).tolist()
    except Exception as e:
        print(f"ERRO em get_available_snapshots: {e}")
        return e # Retorna a exceção

def get_data_for_snapshot(snapshot_date):
    try:
        client = bigquery.Client()
        query = f"SELECT * FROM `{TABELA_RESUMO_ID}` WHERE data_snapshot = @snapshot_date"
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("snapshot_date", "DATE", snapshot_date.date()),
            ]
        )
        df = client.query(query, job_config=job_config).to_dataframe()
        return df
    except Exception as e:
        print(f"ERRO em get_data_for_snapshot: {e}")
        return e # Retorna a exceção

def get_net_history_as_df(category_column_name):
    try:
        client = bigquery.Client()
        query = f"""
            WITH 
            base_com_status AS (
              SELECT data_snapshot, cod_cliente,
                CASE WHEN {category_column_name} = 'CHURN' THEN 'Churn' ELSE 'Ativo' END AS status
              FROM `{TABELA_RESUMO_ID}`
              WHERE {category_column_name} != 'NOVO CLIENTE'
            ),
            snapshots_mensais AS (
              SELECT DATE_TRUNC(data_snapshot, MONTH) as ano_mes, MAX(data_snapshot) as ultimo_snapshot_do_mes
              FROM base_com_status GROUP BY 1
            ),
            contagem_status_mensal AS (
              SELECT m.ano_mes, b.status, COUNT(b.cod_cliente) as contagem
              FROM base_com_status b JOIN snapshots_mensais m ON b.data_snapshot = m.ultimo_snapshot_do_mes
              GROUP BY 1, 2
            )
            SELECT
              ano_mes, IFNULL(Ativo, 0) as Ativo, IFNULL(Churn, 0) as Churn,
              (IFNULL(Ativo, 0) - IFNULL(Churn, 0)) as NET
            FROM (SELECT ano_mes, status, contagem FROM contagem_status_mensal)
            PIVOT(SUM(contagem) FOR status IN ('Ativo', 'Churn'))
            ORDER BY ano_mes
        """
        df = client.query(query).to_dataframe()
        df['ano_mes'] = pd.to_datetime(df['ano_mes'])
        df.set_index('ano_mes', inplace=True)
        return df
    except Exception as e:
        print(f"ERRO ao calcular histórico de NET: {e}")
        return e # Retorna a exceção