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
    categorias = CATEGORIAS_ANTIGO if model_type == 'antigo' else CATEGORIAS_NOVO
    for key, category_name in categorias.items():
        if isinstance(key, int) and score == key:
            return category_name
        elif isinstance(key, tuple) and key[0] <= score <= key[1]:
            return category_name
    return "INDEFINIDO"

def get_customer_segments(df_all_transactions, analysis_date, model_type, focus_type, status_ui=None):
    """
    Orquestra a análise RFV para todos os clientes, reportando o progresso para a UI.
    """
    if status_ui:
        # A mensagem inicial já é bem descritiva
        status_ui.info(f"Analisando: {focus_type} para data de {analysis_date.strftime('%d/%m/%Y')}")

    rules_set = RFV_RULES_NOVO if model_type == 'novo' else RFV_RULES_ANTIGO
    if focus_type not in rules_set:
        if status_ui:
            status_ui.error(f"Erro: O tipo de foco '{focus_type}' não é válido para o modelo '{model_type}'.")
        return pd.DataFrame()

    sku_map = {
        'Cápsulas': ['Cápsula'], 'Insumos': ['Filtro', 'CO2'],
        'Filtro': ['Filtro'], 'Cilindros': ['CO2']
    }
    df_focus = df_all_transactions[df_all_transactions['tipo_sku'].isin(sku_map.get(focus_type, []))].copy()
    
    if df_focus.empty:
        if status_ui:
            status_ui.warning(f"Nenhuma transação encontrada para '{focus_type}'. Pulando...")
        return pd.DataFrame()

    grouped_by_customer = df_focus.groupby('cod_cliente')
    results_list = []
    
    progress_bar = None
    if status_ui:
        # --- MELHORIA AQUI: Texto da barra de progresso mais detalhado ---
        progress_text = f"Calculando RFV de {focus_type} para {len(grouped_by_customer)} clientes..."
        progress_bar = status_ui.progress(0, text=progress_text)
    
    total_customers = len(grouped_by_customer)
    for i, (customer_id, customer_df) in enumerate(grouped_by_customer):
        rfv_result = calculate_customer_rfv(customer_df, analysis_date, rules_set[focus_type])
        rfv_result['cod_cliente'] = customer_id
        results_list.append(rfv_result)
        if progress_bar:
            # A cada 500 clientes, atualizamos o texto para não poluir muito
            if i % 500 == 0:
                progress_bar.progress((i + 1) / total_customers, text=progress_text)
            else:
                progress_bar.progress((i + 1) / total_customers)

    if not results_list:
        if status_ui:
            status_ui.warning("A lista de resultados está vazia após o loop de cálculo.")
        return pd.DataFrame()

    if progress_bar:
        progress_bar.empty() # Limpa a barra de progresso ao final

    df_results = pd.DataFrame(results_list)
    df_results['categoria'] = df_results['Total_score'].apply(lambda score: get_category(score, model_type))

    first_purchase = df_all_transactions.groupby('cod_cliente')['data_compra'].min().rename('data_primeira_compra')
    df_results = df_results.merge(first_purchase, on='cod_cliente', how='left')
    
    analysis_date_dt = pd.to_datetime(analysis_date)
    tenure_days = (analysis_date_dt - df_results['data_primeira_compra']).dt.days
    df_results.loc[tenure_days <= 90, 'categoria'] = 'NOVO CLIENTE'
    
    # Não precisamos mais da mensagem de sucesso aqui, vamos movê-la para o app.py
    
    return df_results[['cod_cliente', 'categoria', 'Total_score', 'R_score', 'F_score', 'V_score', 
                       'recency_days', 'frequency', 'volume']].set_index('cod_cliente')