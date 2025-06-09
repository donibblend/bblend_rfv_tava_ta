# Em app.py

import streamlit as st
import pandas as pd
from datetime import datetime

from core.data_loader import carregar_dados
from core.tava_ta_analyzer import get_customer_segments, get_category

st.set_page_config(layout="wide", page_title="B.blend RFV Tava -> Tá")
st.title("Análise de Migração RFV - Tava -> Tá")

@st.cache_data(show_spinner=False) # Desativamos o spinner padrão aqui
def carregar_dados_completos():
    with st.spinner("Carregando dados do BigQuery... Por favor, aguarde."):
        df = carregar_dados()
        if df is not None:
            df.dropna(subset=['data_compra'], inplace=True)
    return df

df_base_completa = carregar_dados_completos()

if df_base_completa is None:
    st.error("Falha ao carregar os dados do BigQuery.")
    st.stop()

with st.sidebar:
    st.header("Filtros da Análise")
    hoje = datetime.now().date()
    data_ta = st.date_input("Data 'Tá' (Mais Recente)", value=hoje, max_value=hoje)
    data_tava_default = hoje - pd.Timedelta(days=180)
    data_tava = st.date_input("Data 'Tava' (Mais Antiga)", value=data_tava_default, max_value=hoje)

    modelo_rfv_map = {"Modelo Novo (Diamante, Ouro...)": "novo", "Modelo Antigo (Elite, Potencial Elite...)": "antigo"}
    modelo_rfv_label = st.selectbox("Escolha o Modelo RFV:", list(modelo_rfv_map.keys()))
    modelo_rfv_escolhido = modelo_rfv_map[modelo_rfv_label]

    if modelo_rfv_escolhido == 'novo':
        opcoes_foco = ["Geral", "Cápsulas", "Filtro", "Cilindros"]
    else:
        opcoes_foco = ["Geral", "Cápsulas", "Insumos"]
    
    tipo_rfv_foco = st.selectbox("Escolha o Tipo de RFV para Análise:", opcoes_foco)
    processar_btn = st.button("Processar Análise Tava/Tá")

if processar_btn:
    if data_tava >= data_ta:
        st.error("A Data 'Tava' deve ser anterior à Data 'Tá'.")
    else:
        # --- MELHORIA AQUI: Usamos um expander para mostrar os logs detalhados ---
        log_container = st.expander("Ver logs de processamento em tempo real...", expanded=True)
        
        data_tava_dt = pd.to_datetime(data_tava)
        data_ta_dt = pd.to_datetime(data_ta)

        if tipo_rfv_foco == 'Geral':
            componentes = opcoes_foco[1:]
            
            log_container.info(f"FASE 1: Calculando categorias 'Geral' para a data 'Tava' ({data_tava.strftime('%d/%m/%Y')})")
            tava_scores = []
            for componente in componentes:
                df_tava_comp = get_customer_segments(df_base_completa, data_tava, modelo_rfv_escolhido, componente, status_ui=log_container)
                if not df_tava_comp.empty:
                    df_tava_comp.rename(columns={'Total_score': f'score_{componente}'}, inplace=True)
                    tava_scores.append(df_tava_comp[[f'score_{componente}']])
            
            log_container.info(f"FASE 2: Calculando categorias 'Geral' para a data 'Tá' ({data_ta.strftime('%d/%m/%Y')})")
            ta_scores = []
            for componente in componentes:
                df_ta_comp = get_customer_segments(df_base_completa, data_ta, modelo_rfv_escolhido, componente, status_ui=log_container)
                if not df_ta_comp.empty:
                    df_ta_comp.rename(columns={'Total_score': f'score_{componente}'}, inplace=True)
                    ta_scores.append(df_ta_comp[[f'score_{componente}']])

            if not tava_scores or not ta_scores:
                st.warning(f"Não foi possível calcular o RFV 'Geral' por falta de dados em um ou mais componentes.")
                st.stop()
            
            df_tava_geral = pd.concat(tava_scores, axis=1); df_ta_geral = pd.concat(ta_scores, axis=1)
            df_tava_geral['Total_score'] = df_tava_geral.mean(axis=1).round(); df_ta_geral['Total_score'] = df_ta_geral.mean(axis=1).round()
            df_tava = df_tava_geral.reset_index(); df_ta = df_ta_geral.reset_index()
            df_tava['categoria'] = df_tava['Total_score'].apply(lambda score: get_category(score, modelo_rfv_escolhido))
            df_ta['categoria'] = df_ta['Total_score'].apply(lambda score: get_category(score, modelo_rfv_escolhido))
            first_purchase = df_base_completa.groupby('cod_cliente')['data_compra'].min().rename('data_primeira_compra')
            df_tava = df_tava.merge(first_purchase, on='cod_cliente', how='left'); tenure_tava = (data_tava_dt - df_tava['data_primeira_compra']).dt.days; df_tava.loc[tenure_tava <= 90, 'categoria'] = 'NOVO CLIENTE'
            df_ta = df_ta.merge(first_purchase, on='cod_cliente', how='left'); tenure_ta = (data_ta_dt - df_ta['data_primeira_compra']).dt.days; df_ta.loc[tenure_ta <= 90, 'categoria'] = 'NOVO CLIENTE'
        
        else:
            df_tava = get_customer_segments(df_base_completa, data_tava, modelo_rfv_escolhido, tipo_rfv_foco, status_ui=log_container)
            df_ta = get_customer_segments(df_base_completa, data_ta, modelo_rfv_escolhido, tipo_rfv_foco, status_ui=log_container)
            if df_tava.empty or df_ta.empty:
                st.warning(f"Não foram encontradas transações suficientes para a análise de '{tipo_rfv_foco}'.")
                st.stop()
            df_tava.reset_index(inplace=True); df_ta.reset_index(inplace=True)

        log_container.success("Análise concluída! Gerando visualizações...")
        
        df_merged = pd.merge(df_tava[['cod_cliente', 'categoria']], df_ta[['cod_cliente', 'categoria']], on='cod_cliente', how='outer', suffixes=('_tava', '_ta'))
        df_merged['categoria_tava'].fillna('ENTRANTE NA BASE', inplace=True); df_merged['categoria_ta'].fillna('CHURN', inplace=True)
        
        if modelo_rfv_escolhido == 'novo':
            ORDER_Y = ['DIAMANTE', 'OURO', 'PRATA', 'BRONZE', 'NOVO CLIENTE', 'CHURN', 'ENTRANTE NA BASE']
            ORDER_X = ['CHURN', 'NOVO CLIENTE', 'BRONZE', 'PRATA', 'OURO', 'DIAMANTE']
        else:
            ORDER_Y = ['ELITE', 'POTENCIAL ELITE', 'CLIENTE LEAL', 'PROMISSOR', 'PEGANDO NO SONO', 'EM RISCO', 'ADORMECIDO', 'NOVO CLIENTE', 'CHURN', 'ENTRANTE NA BASE']
            ORDER_X = ['CHURN', 'NOVO CLIENTE', 'ADORMECIDO', 'EM RISCO', 'PEGANDO NO SONO', 'PROMISSOR', 'CLIENTE LEAL', 'POTENCIAL ELITE', 'ELITE']
        
        tabela_base = pd.crosstab(df_merged['categoria_tava'], df_merged['categoria_ta'])
        present_y = tabela_base.index.tolist(); present_x = tabela_base.columns.tolist()
        final_order_y = [cat for cat in ORDER_Y if cat in present_y] + sorted([cat for cat in present_y if cat not in ORDER_Y])
        final_order_x = [cat for cat in ORDER_X if cat in present_x] + sorted([cat for cat in present_x if cat not in ORDER_X])
        tabela_reordenada = tabela_base.reindex(index=final_order_y, columns=final_order_x, fill_value=0)
        tabela_absoluta = tabela_reordenada.copy()
        tabela_absoluta.loc['Total',:] = tabela_absoluta.sum(axis=0).astype(int)
        tabela_absoluta['Total'] = tabela_absoluta.sum(axis=1).astype(int)
        tabela_percentual = tabela_reordenada.div(tabela_reordenada.sum(axis=1), axis=0) * 100
        
        st.header(f"Matriz de Migração - {modelo_rfv_label} ({tipo_rfv_foco})")
        st.markdown(f"Análise comparando a base de clientes em **{data_tava.strftime('%d/%m/%Y')} (Tava)** com **{data_ta.strftime('%d/%m/%Y')} (Tá)**.")
        st.subheader("Visão em Números Absolutos")
        st.write("Esta tabela mostra o número total de clientes que migraram de uma categoria (linhas) para outra (colunas).")
        st.dataframe(tabela_absoluta.style.format(lambda x: f"{x:,.0f}".replace(",", ".")).background_gradient(cmap='viridis_r'))
        st.subheader("Visão em Percentual (%)")
        st.write("Esta tabela mostra, para cada categoria 'Tava' (linha), qual a porcentagem de clientes que foi para cada categoria 'Tá' (coluna).")
        st.dataframe(tabela_percentual.style.format('{:.2f}%').background_gradient(cmap='viridis_r'))

else:
    st.info("Por favor, selecione os filtros na barra lateral e clique em 'Processar Análise' para ver os resultados.")