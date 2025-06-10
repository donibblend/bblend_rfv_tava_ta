# Em core/data_loader.py
import pandas as pd
from google.cloud import bigquery

def carregar_dados_historicos():
    """
    Carrega TODOS os dados da tabela de resumo pré-calculada RFV_ANALISE_HISTORICO.
    """
    try:
        client = bigquery.Client()
        tabela_resumo_id = "bblend-data-warehouse-dev.BI_CRM.RFV_ANALISE_HISTORICO"
        print(f"Lendo dados da tabela de resumo: {tabela_resumo_id}")
        
        query = f"SELECT * FROM `{tabela_resumo_id}`"
        
        df = client.query(query).to_dataframe()
        print(f"Dados históricos de RFV carregados com sucesso! {len(df)} linhas retornadas.")

        # Garante que a coluna de data esteja no formato correto
        if 'data_snapshot' in df.columns:
            df['data_snapshot'] = pd.to_datetime(df['data_snapshot'])
        
        return df

    except Exception as e:
        print(f"ERRO ao carregar dados da tabela de resumo RFV: {e}")
        return None