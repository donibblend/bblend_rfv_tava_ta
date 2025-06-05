# Em core/data_loader.py
import pandas as pd
import os

def load_data_from_csv(file_path="amostra_rfv_24k.csv"):
    """
    Carrega os dados de um arquivo CSV local e converte os tipos de coluna.
    """
    # Verifica se o arquivo existe antes de tentar lê-lo
    if not os.path.exists(file_path):
        print(f"--- ERRO ---")
        print(f"Arquivo CSV não encontrado no caminho: '{file_path}'")
        print("Por favor, certifique-se de que você fez o upload do arquivo de amostra para o seu ambiente Codespaces e que o nome do arquivo aqui no código está correto.")
        print("--------------")
        return None

    try:
        print(f"Carregando dados do arquivo local: {file_path}...")
        df = pd.read_csv(file_path)

        # --- Conversões de Tipo de Dados (MUITO IMPORTANTE) ---
        # Converte colunas de data para o formato datetime.
        # errors='coerce' transforma datas que não consegue ler em NaT (Not a Time), evitando erros.
        if 'data_compra' in df.columns:
            df['data_compra'] = pd.to_datetime(df['data_compra'], errors='coerce')
        if 'data_faturamento' in df.columns:
            df['data_faturamento'] = pd.to_datetime(df['data_faturamento'], errors='coerce')
        if 'data_entrega' in df.columns:
            df['data_entrega'] = pd.to_datetime(df['data_entrega'], errors='coerce')

        # Converte colunas numéricas que podem ter sido lidas como texto (object)
        colunas_numericas = ['volume', 'frete_receita', 'custo_produto_unit', 'receita_etiqueta_unit', 'receita_descontada_unit']
        for col in colunas_numericas:
            if col in df.columns:
                # errors='coerce' transforma valores não-numéricos em NaN (Not a Number)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        print(f"Dados carregados com sucesso! {len(df)} linhas lidas.")
        return df

    except Exception as e:
        print(f"Ocorreu um erro inesperado ao ler ou processar o arquivo CSV: {e}")
        return None

# Função principal que será chamada pela aplicação.
def carregar_dados():
    """Função principal para carregar dados. Atualmente configurada para ler do CSV."""
    # Se você renomeou o seu arquivo de amostra, mude o nome aqui:
    return load_data_from_csv(file_path="amostra_rfv_24k.csv")

# --- Bloco de Teste ---
# Este bloco só executa quando você roda o script diretamente (ex: python core/data_loader.py)
if __name__ == '__main__':
    print("--- Testando o carregamento de dados via CSV ---")
    df_teste = carregar_dados()

    if df_teste is not None:
        print("\nCarregamento bem-sucedido. Amostra dos dados:")
        print(df_teste.head())
        print("\nTipos de dados após conversão:")
        print(df_teste.dtypes)
    else:
        print("\nFalha ao carregar dados. Verifique as mensagens de erro acima.")