# Em core/rfv_calculator.py

import pandas as pd
from datetime import datetime
# Importamos as regras que definimos no arquivo anterior
# O '.' antes de rfv_rules indica que é um import relativo, dentro do mesmo pacote 'core'
from .rfv_rules import RFV_RULES_ANTIGO, RFV_RULES_NOVO

# --- Função Auxiliar de Pontuação ---

def get_score(value, rules_dict):
    """
    Função genérica para encontrar a pontuação de um valor com base em um dicionário de regras.
    Exemplo de rules_dict: {(0, 90): 3, (91, 180): 2, (181, 365): 1}
    """
    # Se o valor for 0 (ex: Frequência ou Volume zerados), a pontuação é 0.
    if value == 0:
        return 0
    # Itera sobre os intervalos (ex: (0, 90)) e pontuações (ex: 3) nas regras
    for r, s in rules_dict.items():
        if r[0] <= value <= r[1]:
            return s
    # Se o valor não se encaixar em nenhuma regra (ex: Recência > 365 dias), retorna 0
    return 0

# --- Função Principal de Cálculo ---

def calculate_customer_rfv(df_customer_product_transactions, analysis_date, rules_config):
    """
    Calcula os valores e scores de R, F e V para um único cliente e um tipo de produto.

    Args:
        df_customer_product_transactions (pd.DataFrame): DataFrame com transações APENAS
            do cliente e do tipo de produto que estamos analisando.
        analysis_date (datetime): A data de referência para o cálculo (ex: data "Tava" ou "Tá").
        rules_config (dict): O dicionário de regras para o tipo de produto (ex: RFV_RULES_NOVO['Cápsulas']).

    Returns:
        dict: Um dicionário contendo os valores e scores de R, F e V.
    """
    # Garante que a data de análise seja um objeto datetime para comparações
    analysis_date = pd.to_datetime(analysis_date)

    # Filtra os dados para a janela de 365 dias antes da data de análise
    start_date = analysis_date - pd.Timedelta(days=365)
    df_period = df_customer_product_transactions[
        (df_customer_product_transactions['data_compra'] >= start_date) &
        (df_customer_product_transactions['data_compra'] <= analysis_date)
    ]

    if df_period.empty:
        # Se não houver transações no período, tudo é zero, cliente inativo para este item.
        return {
            'recency_days': -1, # Usamos -1 para indicar que não houve compra no período
            'frequency': 0,
            'volume': 0,
            'R_score': 0,
            'F_score': 0,
            'V_score': 0,
            'Total_score': 0
        }

    # 1. Cálculo da Recência
    last_purchase_date = df_period['data_compra'].max()
    recency_days = (analysis_date.date() - last_purchase_date.date()).days
    r_score = get_score(recency_days, rules_config['R'])

    # 2. Cálculo da Frequência (contamos pedidos únicos)
    frequency = df_period['nf_sap'].nunique()
    f_score = get_score(frequency, rules_config['F'])

    # 3. Cálculo do Volume (somamos a quantidade de itens)
    volume = df_period['volume'].sum()
    v_score = get_score(volume, rules_config['V'])
    
    # 4. Score Total
    total_score = r_score + f_score + v_score

    # Retorna todos os valores calculados em um dicionário
    return {
        'recency_days': recency_days,
        'frequency': int(frequency),
        'volume': int(volume),
        'R_score': r_score,
        'F_score': f_score,
        'V_score': v_score,
        'Total_score': total_score
    }

# --- Bloco de Teste ---
# Este bloco só executa quando você roda o script diretamente (ex: python core/rfv_calculator.py)
# É ótimo para verificar se a lógica está correta sem precisar rodar o app Streamlit inteiro.
if __name__ == '__main__':
    # Criando um DataFrame de exemplo para teste
    data = {
        'data_compra': ['2025-05-15', '2025-05-15', '2025-03-10', '2024-11-01'],
        'nf_sap': ['PEDIDO1', 'PEDIDO1', 'PEDIDO2', 'PEDIDO3'],
        'volume': [10, 5, 12, 8]
    }
    df_teste_cliente = pd.DataFrame(data)
    df_teste_cliente['data_compra'] = pd.to_datetime(df_teste_cliente['data_compra'])

    # Data da análise (hoje, 5 de Junho de 2025)
    data_analise_teste = datetime.strptime('2025-06-05', '%Y-%m-%d')
    
    # Usando as regras de Cápsulas do Modelo Novo para o teste
    regras_teste = RFV_RULES_NOVO['Cápsulas']

    print("--- Testando a função calculate_customer_rfv ---")
    rfv_resultado = calculate_customer_rfv(df_teste_cliente, data_analise_teste, regras_teste)

    print("\nDataFrame de Teste do Cliente:")
    print(df_teste_cliente)
    print(f"\nData da Análise: {data_analise_teste.date()}")
    print("\nRegras Aplicadas (Cápsulas - Modelo Novo):")
    print(regras_teste)
    print("\nResultado do Cálculo RFV:")
    print(rfv_resultado)

    # Verificação manual dos resultados esperados
    # Recência: 05/06/2025 - 15/05/2025 = 21 dias -> Score R = 3
    # Frequência: 3 pedidos únicos (PEDIDO1, PEDIDO2, PEDIDO3) -> Score F = 2
    # Volume: 10 + 5 + 12 + 8 = 35 -> Score V = 1
    # Score Total: 3 + 2 + 1 = 6
    print("\n--- Verificação Manual ---")
    print("Valores Esperados para o Teste:")
    print("Recency_days: 21, R_score: 3")
    print("Frequency: 3, F_score: 2")
    print("Volume: 35, V_score: 1")
    print("Total_score: 6")