# Em core/tava_ta_analyzer.py

import pandas as pd
from tqdm import tqdm  # Biblioteca para criar barras de progresso (muito útil!)
from .rfv_rules import RFV_RULES_ANTIGO, RFV_RULES_NOVO, CATEGORIAS_ANTIGO, CATEGORIAS_NOVO
from .rfv_calculator import calculate_customer_rfv

def get_category(score, model_type):
    """
    Atribui a categoria final (ex: 'DIAMANTE', 'ELITE') com base no score total.
    """
    if score < 3:
        return "CHURN"
    
    # Escolhe o dicionário de categorias correto (antigo ou novo)
    categorias = CATEGORIAS_ANTIGO if model_type == 'antigo' else CATEGORIAS_NOVO
    
    for key, category_name in categorias.items():
        if isinstance(key, int) and score == key:
            return category_name
        elif isinstance(key, tuple) and key[0] <= score <= key[1]:
            return category_name
            
    return "INDEFINIDO"

def get_customer_segments(df_all_transactions, analysis_date, model_type, focus_type):
    """
    Orquestra a análise RFV para todos os clientes para uma data de análise específica.

    Args:
        df_all_transactions (pd.DataFrame): O DataFrame completo com todas as transações.
        analysis_date (datetime): A data de referência para a análise ("Tava" ou "Tá").
        model_type (str): 'antigo' ou 'novo'.
        focus_type (str): O tipo de produto a ser analisado (ex: 'Cápsulas').

    Returns:
        pd.DataFrame: Um DataFrame com cada cliente, seus scores RFV e sua categoria final.
    """
    print(f"Iniciando análise RFV para {analysis_date} com foco em '{focus_type}' e modelo '{model_type}'...")

    # 1. Define qual conjunto de regras usar (Antigo ou Novo)
    rules_set = RFV_RULES_NOVO if model_type == 'novo' else RFV_RULES_ANTIGO
    if focus_type not in rules_set:
        print(f"Erro: O tipo de foco '{focus_type}' não é válido para o modelo '{model_type}'.")
        return pd.DataFrame() # Retorna um DataFrame vazio

    # 2. Filtra as transações para o tipo de produto em foco
    # Mapeamento do 'focus_type' para os valores na coluna 'tipo_sku'
    sku_map = {
        'Cápsulas': ['Cápsula'],
        'Insumos': ['Filtro', 'CO2'],
        'Filtro': ['Filtro'],
        'Cilindros': ['CO2']
    }
    df_focus = df_all_transactions[df_all_transactions['tipo_sku'].isin(sku_map.get(focus_type, []))].copy()
    
    if df_focus.empty:
        print("Nenhuma transação encontrada para o tipo de foco selecionado.")
        return pd.DataFrame()

    # 3. Agrupa as transações por cliente
    grouped_by_customer = df_focus.groupby('cod_cliente')
    
    results_list = []
    
    # tqdm cria uma barra de progresso visual no terminal, útil para longos processamentos
    for customer_id, customer_df in tqdm(grouped_by_customer, desc=f"Calculando RFV para {focus_type}"):
        
        # 4. Calcula o RFV para cada cliente usando a função que já testamos
        rfv_result = calculate_customer_rfv(customer_df, analysis_date, rules_set[focus_type])
        
        rfv_result['cod_cliente'] = customer_id
        results_list.append(rfv_result)
        
    if not results_list:
        print("A lista de resultados está vazia após o loop.")
        return pd.DataFrame()

    # 5. Cria um DataFrame com os resultados de RFV de todos os clientes
    df_results = pd.DataFrame(results_list)
    
    # 6. Atribui a categoria RFV com base no score total
    df_results['categoria'] = df_results['Total_score'].apply(lambda score: get_category(score, model_type))

    # 7. Lógica para "NOVO CLIENTE" (sobrescreve a categoria RFV se aplicável)
    # Pega a data da primeira compra de cada cliente do DataFrame completo
    first_purchase = df_all_transactions.groupby('cod_cliente')['data_compra'].min().rename('data_primeira_compra')
    df_results = df_results.merge(first_purchase, on='cod_cliente', how='left')
    
    analysis_date_dt = pd.to_datetime(analysis_date)
    tenure_days = (analysis_date_dt - df_results['data_primeira_compra']).dt.days
    
    # Se o cliente tem 90 dias ou menos de casa, ele é 'NOVO CLIENTE'
    df_results.loc[tenure_days <= 90, 'categoria'] = 'NOVO CLIENTE'
    
    # Retorna as colunas mais importantes
    return df_results[[
        'cod_cliente', 'categoria', 'Total_score', 'R_score', 'F_score', 'V_score', 
        'recency_days', 'frequency', 'volume'
    ]].set_index('cod_cliente')