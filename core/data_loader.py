# Em core/data_loader.py
import pandas as pd
from google.cloud import bigquery

TABELA_RESUMO_ID = "bblend-data-warehouse-dev.BI_CRM.RFV_ANALISE_HISTORICO"

def get_available_snapshots():
    """Busca apenas a lista de datas de snapshot disponíveis para popular os filtros."""
    try:
        client = bigquery.Client()
        query = f"SELECT DISTINCT data_snapshot FROM `{TABELA_RESUMO_ID}` ORDER BY data_snapshot DESC"
        df = client.query(query).to_dataframe()
        return pd.to_datetime(df['data_snapshot']).tolist()
    except Exception as e:
        print(f"ERRO ao buscar snapshots disponíveis: {e}")
        return []

def get_data_for_snapshot(snapshot_date):
    """Busca os dados de RFV para UMA ÚNICA data de snapshot."""
    try:
        client = bigquery.Client()
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
        return df
    except Exception as e:
        print(f"ERRO ao buscar dados para o snapshot {snapshot_date.date()}: {e}")
        return None

def get_net_history_as_df(category_column_name):
    """
    Executa uma query no BigQuery que já calcula o histórico mensal do NET.
    Retorna um DataFrame pequeno, pronto para o gráfico.
    """
    try:
        client = bigquery.Client()
        query = f"""
            WITH 
            base_com_status AS (
              -- Primeiro, define o status de cada cliente em cada snapshot, excluindo 'NOVO CLIENTE'
              SELECT 
                data_snapshot,
                cod_cliente,
                CASE 
                  WHEN {category_column_name} = 'CHURN' THEN 'Churn'
                  ELSE 'Ativo' 
                END AS status
              FROM `{TABELA_RESUMO_ID}`
              WHERE {category_column_name} != 'NOVO CLIENTE'
            ),
            snapshots_mensais AS (
              -- Encontra o último snapshot de cada mês para representar aquele mês
              SELECT 
                DATE_TRUNC(data_snapshot, MONTH) as ano_mes,
                MAX(data_snapshot) as ultimo_snapshot_do_mes
              FROM base_com_status
              GROUP BY 1
            ),
            contagem_status_mensal AS (
              -- Conta Ativos e Churn para cada último snapshot do mês
              SELECT
                m.ano_mes,
                b.status,
                COUNT(b.cod_cliente) as contagem
              FROM base_com_status b
              JOIN snapshots_mensais m ON b.data_snapshot = m.ultimo_snapshot_do_mes
              GROUP BY 1, 2
            )
            -- Pivota a tabela para ter colunas de Ativo e Churn e calcula o NET
            SELECT
              ano_mes,
              IFNULL(Ativo, 0) as Ativo,
              IFNULL(Churn, 0) as Churn,
              (IFNULL(Ativo, 0) - IFNULL(Churn, 0)) as NET
            FROM (
              SELECT ano_mes, status, contagem FROM contagem_status_mensal
            )
            PIVOT(
              SUM(contagem) FOR status IN ('Ativo', 'Churn')
            )
            ORDER BY ano_mes
        """
        df = client.query(query).to_dataframe()
        # Define a data como índice para o gráfico
        df['ano_mes'] = pd.to_datetime(df['ano_mes'])
        df.set_index('ano_mes', inplace=True)
        return df
    except Exception as e:
        print(f"ERRO ao calcular histórico de NET: {e}")
        return pd.DataFrame() # Retorna dataframe vazio em caso de erro