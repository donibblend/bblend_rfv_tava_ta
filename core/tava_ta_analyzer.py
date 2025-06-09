# Em core/tava_ta_analyzer.py

import pandas as pd
from tqdm import tqdm
from .rfv_rules import RFV_RULES_ANTIGO, RFV_RULES_NOVO, CATEGORIAS_ANTIGO, CATEGORIAS_NOVO
from .rfv_calculator import calculate_customer_rfv

def get_category(score, model_type):
    if score < 3: return "CHURN"
    categorias = CATEGORIAS_ANTIGO if model_type == 'antigo' else CATEGORIAS_NOVO
    for key, category_name in categorias.items():
        if isinstance(key, int) and score == key: return category_name
        elif isinstance(key, tuple) and key[0] <= score <= key[1]: return category_name
    return "INDEFINIDO"

def get_customer_segments(df_all_transactions, analysis_date, model_type, focus_type, status_ui=None):
    if status_ui:
        status_ui.info(f"Analisando: {focus_type} para data de {analysis_date.strftime('%d/%m/%Y')}")

    rules_set = RFV_RULES_NOVO if model_type == 'novo' else RFV_RULES_ANTIGO
    if focus_type not in rules_set:
        if status_ui: status_ui.error(f"Erro: Foco '{focus_type}' inválido para o modelo '{model_type}'.")
        return pd.DataFrame()

    # --- INÍCIO DA MUDANÇA DE LÓGICA ---
    
    # 1. Pega a lista completa de TODOS os clientes da base de dados geral
    all_customer_ids = df_all_transactions['cod_cliente'].unique()
    
    # 2. Filtra as transações para o tipo de produto em foco
    sku_map = {'Cápsulas': ['Cápsula'], 'Insumos': ['Filtro', 'CO2'], 'Filtro': ['Filtro'], 'Cilindros': ['CO2']}
    df_focus = df_all_transactions[df_all_transactions['tipo_sku'].isin(sku_map.get(focus_type, []))]
    
    # 3. Cria um conjunto de clientes que compraram o produto em foco, para consulta rápida
    customers_in_focus = set(df_focus['cod_cliente'].unique())
    grouped_by_customer_in_focus = df_focus.groupby('cod_cliente')
    
    # --- FIM DA MUDANÇA DE LÓGICA ---

    results_list = []
    
    progress_bar = None
    if status_ui:
        progress_text = f"Processando {len(all_customer_ids)} clientes para '{focus_type}'..."
        progress_bar = status_ui.progress(0, text=progress_text)
    
    # 4. Itera sobre TODOS os clientes, não apenas os do foco
    for i, customer_id in enumerate(all_customer_ids):
        if customer_id in customers_in_focus:
            # Cliente comprou este produto, calcula RFV normalmente
            customer_df = grouped_by_customer_in_focus.get_group(customer_id)
            rfv_result = calculate_customer_rfv(customer_df, analysis_date, rules_set[focus_type])
            rfv_result['cod_cliente'] = customer_id
        else:
            # Cliente NUNCA comprou este produto. Ele é CHURN para este foco.
            rfv_result = {'cod_cliente': customer_id, 'recency_days': -1, 'frequency': 0, 'volume': 0,
                          'R_score': 0, 'F_score': 0, 'V_score': 0, 'Total_score': 0}
        
        results_list.append(rfv_result)
        
        if progress_bar and i % 500 == 0:
            progress_bar.progress((i + 1) / len(all_customer_ids), text=progress_text)

    if progress_bar: progress_bar.empty()

    df_results = pd.DataFrame(results_list)
    df_results['categoria'] = df_results['Total_score'].apply(lambda score: get_category(score, model_type))

    first_purchase = df_all_transactions.groupby('cod_cliente')['data_compra'].min().rename('data_primeira_compra')
    df_results = df_results.merge(first_purchase, on='cod_cliente', how='left')
    
    analysis_date_dt = pd.to_datetime(analysis_date)
    tenure_days = (analysis_date_dt - df_results['data_primeira_compra']).dt.days
    df_results.loc[tenure_days <= 90, 'categoria'] = 'NOVO CLIENTE'
    
    return df_results[['cod_cliente', 'categoria', 'Total_score', 'R_score', 'F_score', 'V_score', 
                       'recency_days', 'frequency', 'volume']].set_index('cod_cliente')