import os
from dotenv import load_dotenv
from google.cloud import bigquery
import pandas as pd

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

def get_bigquery_client():
    """
    Cria e retorna um cliente BigQuery.
    A autenticação será feita via Application Default Credentials (ADC)
    se GOOGLE_APPLICATION_CREDENTIALS não estiver definido no ambiente.
    """
    try:
        project_id = os.getenv("BIGQUERY_PROJECT_ID")
        # Se você precisar especificar o projeto para o cliente explicitamente:
        # client = bigquery.Client(project=project_id)
        client = bigquery.Client()
        print(f"Cliente BigQuery criado com sucesso para o projeto: {client.project}")
        return client
    except Exception as e:
        print(f"Erro ao criar cliente BigQuery: {e}")
        return None

def load_data_from_bq(limit=None):
    """
    Carrega dados da tabela especificada no BigQuery.
    Aplica um limite de linhas se especificado.
    """
    client = get_bigquery_client()
    if not client:
        return None

    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    dataset_id = os.getenv("BIGQUERY_DATASET_ID")
    table_id = os.getenv("BIGQUERY_TABLE_ID")

    if not all([project_id, dataset_id, table_id]):
        print("Erro: Variáveis de ambiente do BigQuery não configuradas corretamente.")
        return None

    table_full_id = f"{project_id}.{dataset_id}.{table_id}"
    print(f"Tentando carregar dados de: {table_full_id}")

    query = f"SELECT * FROM `{table_full_id}`"
    if limit:
        query += f" LIMIT {limit}"

    try:
        print(f"Executando query: {query}")
        query_job = client.query(query)
        df = query_job.to_dataframe()
        print(f"Dados carregados com sucesso! {len(df)} linhas retornadas.")
        return df
    except Exception as e:
        print(f"Erro ao executar query ou converter para DataFrame: {e}")
        return None

if __name__ == '__main__':
    # Este bloco é para teste direto do script
    print("Testando o carregamento de dados do BigQuery...")
    # Teste carregando apenas 5 linhas para ser rápido
    df_sample = load_data_from_bq(limit=5)

    if df_sample is not None:
        print("\nAmostra dos dados carregados:")
        print(df_sample.head())
        print(f"\nColunas: {df_sample.columns.tolist()}")
        print(f"\nTipos de dados por coluna:\n{df_sample.dtypes}")
    else:
        print("\nFalha ao carregar dados.")