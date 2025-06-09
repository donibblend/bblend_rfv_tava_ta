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
        status_ui.write(f"Iniciando análise para **{focus_type}** (Data: {analysis_date.strftime('%d/%m/%Y')})...")

    rules_set = RFV_RULES_NOVO if model_type == 'novo' else RFV_RULES_ANTIGO
    if focus_type not in rules_set:
        if status_ui: status_ui.error(f"Erro: Foco '{focus_type}' inválido para o modelo '{model_type}'.")
        return pd.DataFrame()

    sku_map = {'Cápsulas': ['Cápsula'], 'Insumos': ['Filtro', 'CO2'], 'Filtro': ['Filtro'], 'Cilindros': ['CO2']}
    df_focus = df_all_transactions[df_all_transactions['tipo_sku'].isin(sku_map.get(focus_type, []))]
    
    if df_focus.empty:
        if status_ui: status_ui.warning(f"AVISO: Nenhuma transação encontrada para '{focus_type}'.")
        return pd.DataFrame()

    all_customer_ids = df_all_transactions['cod_cliente'].unique()
    customers_in_focus = set(df_focus['cod_cliente'].unique())
    grouped_by_customer_in_focus = df_focus.groupby('cod_cliente')
    
    results_list = []
    
    progress_bar = None
    if status_ui:
        # --- MELHORIA AQUI: Texto da barra de progresso mais específico ---
        progress_text = f"Processando {len(all_customer_ids)} clientes para a análise de '{focus_type}'..."
        progress_bar = status_ui.progress(0, text=progress_text)
    
    for i, customer_id in enumerate(all_customer_ids):
        if customer_id in customers_in_focus:
            customer_df = grouped_by_customer_in_focus.get_group(customer_id)
            rfv_result = calculate_customer_rfv(customer_df, analysis_date, rules_set[focus_type])
            rfv_result['cod_cliente'] = customer_id
        else:
            rfv_result = {'cod_cliente': customer_id, 'Total_score': 0}
        
        results_list.append(rfv_result)
        
        if progress_bar:
            progress_bar.progress((i + 1) / len(all_customer_ids))

    if progress_bar: progress_bar.empty()

    df_results = pd.DataFrame(results_list)
    df_results['categoria'] = df_results['Total_score'].apply(lambda score: get_category(score, model_type))

    first_purchase = df_all_transactions.groupby('cod_cliente')['data_compra'].min().rename('data_primeira_compra')
    df_results = df_results.merge(first_purchase, on='cod_cliente', how='left')
    
    analysis_date_dt = pd.to_datetime(analysis_date)
    # Garante que não há NaT na data da primeira compra para o cálculo do tenure
    df_results['data_primeira_compra'].dropna(inplace=True)
    tenure_days = (analysis_date_dt - df_results['data_primeira_compra']).dt.days
    df_results.loc[tenure_days <= 90, 'categoria'] = 'NOVO CLIENTE'
    
    return df_results[['cod_cliente', 'categoria', 'Total_score']].set_index('cod_cliente')