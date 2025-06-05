# Em app.py

import streamlit as st
import pandas as pd
# 1. Mude o import para a nossa nova função principal
from core.data_loader import carregar_dados

# Configuração da página
st.set_page_config(layout="wide", page_title="B.blend RFV Tava/Tá")

# Título da Aplicação
st.title("Análise RFV B.blend - Tava vs. Tá")

# --- Carregamento de Dados ---
# Usaremos st.cache_data para carregar os dados do CSV apenas uma vez e otimizar
@st.cache_data
def carregar_dados_completos():
    """
    Função para carregar os dados, agora usando a função principal do data_loader
    que está configurada para ler do arquivo CSV local.
    """
    # 2. Agora chama nossa função principal que está configurada para CSV
    df = carregar_dados()
    return df

# Chama a função para carregar os dados
df_base_completa = carregar_dados_completos()

# Verifica se os dados foram carregados e mostra uma amostra
if df_base_completa is not None:
    st.success(f"Dados carregados com sucesso do arquivo CSV! {len(df_base_completa)} linhas processadas.")
    st.subheader("Amostra dos Dados Carregados:")
    st.dataframe(df_base_completa.head())
else:
    st.error("Falha ao carregar os dados do arquivo CSV. Verifique o terminal para erros.")

# --- Barra Lateral para Inputs do Usuário ---
st.sidebar.header("Filtros da Análise")

data_tava = st.sidebar.date_input("Data 'Tava' (Mais Antiga)")
data_ta = st.sidebar.date_input("Data 'Tá' (Mais Recente)")

modelo_rfv_escolhido = st.sidebar.selectbox(
    "Escolha o Modelo RFV:",
    ("Modelo Novo (Diamante, Ouro...)", "Modelo Antigo (Elite, Potencial Elite...)")
)

tipo_rfv_foco = st.sidebar.selectbox(
    "Escolha o Tipo de RFV para Análise:",
    ("Geral", "Cápsulas", "Filtro (Novo Modelo)", "Cilindro (Novo Modelo)", "Insumos (Antigo Modelo)")
)

if st.sidebar.button("Processar Análise Tava/Tá"):
    st.sidebar.write("Processando...") # Placeholder para a lógica futura
    # Aqui virá a lógica para chamar as funções de cálculo RFV e análise Tava/Tá
    st.subheader("Resultados da Análise (Placeholder)")
    st.write(f"Analisando de {data_tava} para {data_ta}")
    st.write(f"Modelo: {modelo_rfv_escolhido}, Foco: {tipo_rfv_foco}")
    # Exibir a tabela de resultados aqui