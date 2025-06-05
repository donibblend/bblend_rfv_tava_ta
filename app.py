import streamlit as st
import pandas as pd
from core.data_loader import load_data_from_bq # Importa nossa função

# Configuração da página (opcional, mas bom para começar)
st.set_page_config(layout="wide", page_title="B.blend RFV Tava/Tá")

# Título da Aplicação
st.title("Análise RFV B.blend - Tava vs. Tá")

# --- Carregamento de Dados ---
# Usaremos st.cache_data para carregar os dados apenas uma vez e otimizar
@st.cache_data # Cacheia o resultado da função
def carregar_dados_completos():
    # Por enquanto, vamos carregar uma amostra para agilizar o desenvolvimento.
    # Remova ou aumente o 'limit' quando quiser processar todos os dados.
    df = load_data_from_bq(limit=1000) # Carrega os primeiros 1000 registros
    if df is not None:
        # Converter 'data_compra' para datetime se ainda não estiver
        if 'data_compra' in df.columns:
            df['data_compra'] = pd.to_datetime(df['data_compra'], errors='coerce')
        # Adicionar outras conversões de tipo necessárias aqui
    return df

df_base_completa = carregar_dados_completos()

if df_base_completa is not None:
    st.success(f"Dados carregados com sucesso! {len(df_base_completa)} linhas iniciais processadas.")
    st.subheader("Amostra dos Dados Carregados:")
    st.dataframe(df_base_completa.head())
else:
    st.error("Falha ao carregar os dados do BigQuery. Verifique os logs no terminal.")

# --- Barra Lateral para Inputs do Usuário ---
st.sidebar.header("Filtros da Análise")

data_tava = st.sidebar.date_input("Data 'Tava' (Mais Antiga)")
data_ta = st.sidebar.date_input("Data 'Tá' (Mais Recente)")

modelo_rfv_escolhido = st.sidebar.selectbox(
    "Escolha o Modelo RFV:",
    ("Modelo Novo (Diamante, Ouro...)", "Modelo Antigo (Elite, Potencial Elite...)")
)

# Os tipos de RFV podem depender do modelo escolhido,
# mas vamos simplificar por agora.
tipo_rfv_foco = st.sidebar.selectbox(
    "Escolha o Tipo de RFV para Análise:",
    ("Geral", "Cápsulas", "Filtro (Novo Modelo)", "Cilindro (Novo Modelo)", "Insumos (Antigo Modelo)")
)

if st.sidebar.button("Processar Análise Tava/Tá"):
    st.sidebar.write("Processando...") # Placeholder
    # Aqui virá a lógica para chamar as funções de cálculo RFV e análise Tava/Tá
    # Ex: processar_analise_tava_ta(df_base_completa, data_tava, data_ta, modelo_rfv_escolhido, tipo_rfv_foco)
    st.subheader("Resultados da Análise (Placeholder)")
    st.write(f"Analisando de {data_tava} para {data_ta}")
    st.write(f"Modelo: {modelo_rfv_escolhido}, Foco: {tipo_rfv_foco}")
    # Exibir a tabela de resultados aqui