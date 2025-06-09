# Em core/data_loader.py
import pandas as pd
from google.cloud import bigquery
import os

def load_data_from_bq():
    """
    Carrega TODOS os dados da tabela especificada no BigQuery.
    A autenticação no Cloud Run será feita automaticamente pela conta de serviço.
    """
    try:
        # As credenciais são gerenciadas pelo ambiente do Cloud Run.
        client = bigquery.Client()
        
        # Estas variáveis podem ser configuradas no próprio Cloud Run no futuro,
        # mas por enquanto vamos lê-las do código.
        project_id = "bblend-data-warehouse-dev"
        dataset_id = "BI_CRM"
        table_id = "BaseGemini"

        table_full_id = f"{project_id}.{dataset_id}.{table_id}"
        print(f"Conectando ao BigQuery e carregando dados de: {table_full_id}")

        # Query para pegar todos os dados
        query = f"SELECT * FROM `{table_full_id}`"
        
        query_job = client.query(query)
        df = query_job.to_dataframe()
        
        print(f"Dados carregados com sucesso do BigQuery! {len(df)} linhas retornadas.")

        # --- Conversões de Tipo de Dados (MUITO IMPORTANTE) ---
        if 'data_compra' in df.columns:
            df['data_compra'] = pd.to_datetime(df['data_compra'], errors='coerce')
        # Adicione outras conversões de data se necessário
        
        colunas_numericas = ['volume', 'frete_receita', 'custo_produto_unit', 'receita_etiqueta_unit', 'receita_descontada_unit']
        for col in colunas_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    except Exception as e:
        print(f"ERRO ao conectar ou carregar dados do BigQuery: {e}")
        return None

# Função principal que será chamada pela aplicação
def carregar_dados():
    """Função principal para carregar dados. Agora configurada para o BigQuery."""
    return load_data_from_bq()