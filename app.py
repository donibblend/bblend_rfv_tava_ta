# Em app.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Importa nossas funções principais de lógica
from core.data_loader import carregar_dados
from core.tava_ta_analyzer import get_customer_segments, get_category

# --- Configuração Inicial da Página ---
st.set_page_config(layout="wide", page_title="B.blend RFV Tava/Tá")
st.title("Análise de Migração RFV - Tava vs. Tá")

# --- Carregamento de Dados ---
@st.cache_data
def carregar_dados_completos():
    df = carregar_dados()
    if df is not None:
        df.dropna(subset=['data_compra'], inplace=True)
    return df

df_base_completa = carregar_dados_completos()

if df_base_completa is None:
    st.error("Falha ao carregar os dados do arquivo CSV. Verifique o terminal para erros e se o arquivo está no lugar certo.")
    st.stop()

# --- Barra Lateral para Inputs do Usuário ---
with st.sidebar:
    st.header("Filtros da Análise")

    hoje = datetime.now().date()

    data_ta = st.date_input("Data 'Tá' (Mais Recente)", value=hoje, max_value=hoje)
    # Definindo uma data padrão para 'Tava' para evitar erros na primeira execução
    data_tava_default = hoje - pd.Timedelta(days=180)
    data_tava = st.date_input("Data 'Tava' (Mais Antiga)", value=data_tava_default, max_value=hoje)

    modelo_rfv_map = {
        "Modelo Novo (Diamante, Ouro...)": "novo",
        "Modelo Antigo (Elite, Potencial Elite...)": "antigo"
    }
    modelo_rfv_label = st.selectbox("Escolha o Modelo RFV:", list(modelo_rfv_map.keys()))
    modelo_rfv_escolhido = modelo_rfv_map[modelo_rfv_label]

    if modelo_rfv_escolhido == 'novo':
        opcoes_foco = ["Geral", "Cápsulas", "Filtro", "Cilindros"]
    else:
        opcoes_foco = ["Geral", "Cápsulas", "Insumos"]
    
    tipo_rfv_foco = st.selectbox("Escolha o Tipo de RFV para Análise:", opcoes_foco)

    processar_btn = st.button("Processar Análise Tava/Tá")

# --- Lógica Principal e Exibição de Resultados ---

if processar_btn:
    if data_tava >= data_ta:
        st.error("A Data 'Tava' deve ser anterior à Data 'Tá'.")
    else:
        with st.spinner(f"Processando análise... Isso pode levar alguns minutos."):
            
            # LÓGICA PARA RFV "GERAL"
            if tipo_rfv_foco == 'Geral':
                componentes = opcoes_foco[1:]
                
                tava_scores = []
                ta_scores = []
                for componente in componentes:
                    df_tava_comp = get_customer_segments(df_base_completa, data_tava, modelo_rfv_escolhido, componente)
                    df_ta_comp = get_customer_segments(df_base_completa, data_ta, modelo_rfv_escolhido, componente)
                    
                    # --- INÍCIO DA CORREÇÃO ---
                    # Verifica se o DataFrame retornado não está vazio antes de tentar usá-lo
                    if not df_tava_comp.empty:
                        df_tava_comp.rename(columns={'Total_score': f'score_{componente}'}, inplace=True)
                        tava_scores.append(df_tava_comp[[f'score_{componente}']])
                    
                    if not df_ta_comp.empty:
                        df_ta_comp.rename(columns={'Total_score': f'score_{componente}'}, inplace=True)
                        ta_scores.append(df_ta_comp[[f'score_{componente}']])
                    # --- FIM DA CORREÇÃO ---

                # Verifica se conseguimos calcular o score para pelo menos um componente
                if not tava_scores or not ta_scores:
                    st.warning(f"Não foi possível calcular o RFV 'Geral', pois faltam dados para um ou mais componentes na amostra (ex: 'Cilindros'). Por favor, tente analisar um componente específico, como 'Cápsulas'.")
                    st.stop()
                    
                df_tava_geral = pd.concat(tava_scores, axis=1)
                df_ta_geral = pd.concat(ta_scores, axis=1)

                df_tava_geral['Total_score'] = df_tava_geral.mean(axis=1).round()
                df_ta_geral['Total_score'] = df_ta_geral.mean(axis=1).round()

                df_tava = df_tava_geral.reset_index()
                df_ta = df_ta_geral.reset_index()
                df_tava['categoria'] = df_tava['Total_score'].apply(lambda score: get_category(score, modelo_rfv_escolhido))
                df_ta['categoria'] = df_ta['Total_score'].apply(lambda score: get_category(score, modelo_rfv_escolhido))
            
            # LÓGICA PARA RFV DE PRODUTO ESPECÍFICO
            else:
                df_tava = get_customer_segments(df_base_completa, data_tava, modelo_rfv_escolhido, tipo_rfv_foco)
                df_ta = get_customer_segments(df_base_completa, data_ta, modelo_rfv_escolhido, tipo_rfv_foco)

                if df_tava.empty or df_ta.empty:
                    st.warning(f"Não foram encontradas transações suficientes para a análise de '{tipo_rfv_foco}' no período selecionado.")
                    st.stop()
                
                df_tava.reset_index(inplace=True)
                df_ta.reset_index(inplace=True)

            # --- Construção da Matriz de Transição ---
            df_merged = pd.merge(
                df_tava[['cod_cliente', 'categoria']],
                df_ta[['cod_cliente', 'categoria']],
                on='cod_cliente',
                how='outer',
                suffixes=('_tava', '_ta')
            )
            
            df_merged['categoria_tava'].fillna('ENTRANTE NA BASE', inplace=True)
            df_merged['categoria_ta'].fillna('CHURN', inplace=True)

            st.header(f"Matriz de Migração - {modelo_rfv_label} ({tipo_rfv_foco})")
            st.markdown(f"Análise comparando a base de clientes em **{data_tava.strftime('%d/%m/%Y')} (Tava)** com **{data_ta.strftime('%d/%m/%Y')} (Tá)**.")

            tabela_absoluta = pd.crosstab(df_merged['categoria_tava'], df_merged['categoria_ta'])
            tabela_percentual = pd.crosstab(df_merged['categoria_tava'], df_merged['categoria_ta'], normalize='index') * 100
            
            st.subheader("Visão em Números Absolutos")
            st.write("Esta tabela mostra o número total de clientes que migraram de uma categoria (linhas) para outra (colunas).")
            st.dataframe(tabela_absoluta.style.format(precision=0).background_gradient(cmap='viridis', axis=1))

            st.subheader("Visão em Percentual (%)")
            st.write("Esta tabela mostra, para cada categoria 'Tava' (linha), qual a porcentagem de clientes que foi para cada categoria 'Tá' (coluna). A soma de cada linha é 100%.")
            st.dataframe(tabela_percentual.style.format('{:.2f}%').background_gradient(cmap='viridis', axis=1))

else:
    st.info("Por favor, selecione os filtros na barra lateral e clique em 'Processar Análise' para ver os resultados.")