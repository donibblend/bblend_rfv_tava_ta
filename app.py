# Em app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Importa a única função que precisamos do nosso data_loader
from core.data_loader import carregar_dados_historicos

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="B.blend RFV Tava -> Tá")
st.title("Análise de Migração RFV - B.blend")

# --- Carregamento Único dos Dados ---
@st.cache_data(show_spinner="Carregando histórico de RFV do BigQuery...")
def carregar_dados_completos():
    # Chama a função correta
    df = carregar_dados_historicos()
    if df is not None and not df.empty:
        df.sort_values(by='data_snapshot', ascending=False, inplace=True)
    return df

# Esta é a variável principal com todos os dados, que será usada em todo o app
df_historico_completo = carregar_dados_completos()

if df_historico_completo is None or df_historico_completo.empty:
    st.error("Falha ao carregar o histórico de RFV do BigQuery.")
    st.stop()

# --- Barra Lateral (Sidebar) ---
with st.sidebar:
    st.header("Filtros da Análise")
    
    opcoes_snapshot_disponiveis = pd.to_datetime(df_historico_completo['data_snapshot'].unique())
    
    st.caption(f"Dados atualizados pela última vez em: {opcoes_snapshot_disponiveis[0].strftime('%d/%m/%Y')}")
    
    opcoes_label_map = {
        f"Semana {dt.isocalendar().week:02d} ({dt.strftime('%d/%m/%Y')})": dt 
        for dt in opcoes_snapshot_disponiveis
    }

    st.subheader("Filtros Gerais de Análise")
    modelo_rfv_map = {"Modelo Novo": "novo", "Modelo Antigo": "antigo"}
    modelo_rfv_label = st.selectbox("Escolha o Modelo RFV:", list(modelo_rfv_map.keys()))
    
    if modelo_rfv_label == "Modelo Novo":
        opcoes_foco_map = {"Geral": "categoria_geral_novo", "Cápsulas": "categoria_capsulas_novo", "Filtro": "categoria_filtro_novo", "Cilindros": "categoria_cilindro_novo"}
    else: # Modelo Antigo
        opcoes_foco_map = {"Geral": "categoria_geral_antigo", "Cápsulas": "categoria_capsulas_antigo", "Insumos": "categoria_insumos_antigo"}

    tipo_rfv_foco_label = st.selectbox("Escolha o Tipo de RFV para Análise:", list(opcoes_foco_map.keys()))
    coluna_categoria_selecionada = opcoes_foco_map[tipo_rfv_foco_label]

# --- Criação das Abas ---
tab_matriz, tab_net = st.tabs(["Matriz de Migração", "Histórico de NET"])

# --- Conteúdo da Aba 1: Matriz de Migração ---
with tab_matriz:
    st.header("Análise de Migração 'Tava -> Tá'")
    st.markdown("Selecione os snapshots 'Tava' e 'Tá' abaixo para comparar a evolução dos clientes entre as categorias.")
    
    col_tava, col_ta = st.columns(2)
    with col_ta:
        opcao_ta_label = st.selectbox("Selecione o snapshot 'Tá':", options=list(opcoes_label_map.keys()), index=0, key="select_ta")
        data_ta_selecionada = opcoes_label_map[opcao_ta_label]
    
    with col_tava:
        opcoes_tava_disponiveis = {label: dt for label, dt in opcoes_label_map.items() if dt < data_ta_selecionada}
        data_tava_selecionada = None
        if opcoes_tava_disponiveis:
            opcao_tava_label = st.selectbox("Selecione o snapshot 'Tava':", options=list(opcoes_tava_disponiveis.keys()), index=0, key="select_tava")
            data_tava_selecionada = opcoes_tava_disponiveis[opcao_tava_label]
        else:
            st.warning("Não há snapshots anteriores para comparação.")

    if st.button("Processar Análise de Migração", key="btn_matriz"):
        if data_tava_selecionada:
            with st.spinner("Gerando matriz de migração..."):
                # Filtra o dataframe JÁ CARREGADO em vez de buscar no BQ de novo
                df_tava = df_historico_completo[df_historico_completo['data_snapshot'] == data_tava_selecionada]
                df_ta = df_historico_completo[df_historico_completo['data_snapshot'] == data_ta_selecionada]

                df_tava_segmento = df_tava[['cod_cliente', coluna_categoria_selecionada]].rename(columns={coluna_categoria_selecionada: 'categoria'})
                df_ta_segmento = df_ta[['cod_cliente', coluna_categoria_selecionada]].rename(columns={coluna_categoria_selecionada: 'categoria'})
                df_merged = pd.merge(df_tava_segmento, df_ta_segmento, on='cod_cliente', how='outer', suffixes=('_tava', '_ta'))
                df_merged['categoria_tava'].fillna('ENTRANTE NA BASE', inplace=True); df_merged['categoria_ta'].fillna('CHURN', inplace=True)
                
                if modelo_rfv_label == 'Modelo Novo':
                    ORDER_Y = ['DIAMANTE', 'OURO', 'PRATA', 'BRONZE', 'NOVO CLIENTE', 'CHURN', 'ENTRANTE NA BASE']
                    ORDER_X = ['CHURN', 'NOVO CLIENTE', 'BRONZE', 'PRATA', 'OURO', 'DIAMANTE']
                else:
                    ORDER_Y = ['ELITE', 'POTENCIAL ELITE', 'CLIENTE LEAL', 'PROMISSOR', 'PEGANDO NO SONO', 'EM RISCO', 'ADORMECIDO', 'NOVO CLIENTE', 'CHURN', 'ENTRANTE NA BASE']
                    ORDER_X = ['CHURN', 'NOVO CLIENTE', 'ADORMECIDO', 'EM RISCO', 'PEGANDO NO SONO', 'PROMISSOR', 'CLIENTE LEAL', 'POTENCIAL ELITE', 'ELITE']
                
                st.markdown(f"##### Análise comparando **{data_tava_selecionada.strftime('%d/%m/%Y')} (Tava)** com **{data_ta_selecionada.strftime('%d/%m/%Y')} (Tá)**.")
                tabela_base = pd.crosstab(df_merged['categoria_tava'], df_merged['categoria_ta'])
                present_y = tabela_base.index.tolist(); present_x = tabela_base.columns.tolist()
                final_order_y = [cat for cat in ORDER_Y if cat in present_y] + sorted([cat for cat in present_y if cat not in ORDER_Y])
                final_order_x = [cat for cat in ORDER_X if cat in present_x] + sorted([cat for cat in present_x if cat not in ORDER_X])
                tabela_reordenada = tabela_base.reindex(index=final_order_y, columns=final_order_x, fill_value=0)
                tabela_absoluta = tabela_reordenada.copy()
                tabela_absoluta.loc['Total',:] = tabela_absoluta.sum(axis=0).astype(int)
                tabela_absoluta['Total'] = tabela_absoluta.sum(axis=1).astype(int)
                tabela_percentual = tabela_reordenada.div(tabela_reordenada.sum(axis=1), axis=0).fillna(0) * 100
                
                st.subheader("Visão em Números Absolutos"); st.dataframe(tabela_absoluta.style.format(lambda x: f"{x:,.0f}".replace(",", ".")).background_gradient(cmap='viridis_r'))
                st.subheader("Visão em Percentual (%)"); st.dataframe(tabela_percentual.style.format('{:.2f}%').background_gradient(cmap='viridis_r'))
        else:
            st.warning("Por favor, selecione um período 'Tava' válido para gerar a matriz.")

# --- Conteúdo da Aba 2: Histórico de NET ---
with tab_net:
    st.header("Histórico Mensal de NET (Clientes Ativos - Clientes em Churn)")
    st.info(f"O gráfico abaixo mostra a evolução do NET para a análise de '{tipo_rfv_foco_label}' do '{modelo_rfv_label}'. Clientes na categoria 'NOVO CLIENTE' são excluídos deste cálculo.")
    
    if st.button("Gerar Gráfico Histórico de NET", key="btn_net"):
        with st.spinner("Calculando histórico de NET..."):
            df_filtrado = df_historico_completo[df_historico_completo[coluna_categoria_selecionada] != 'NOVO CLIENTE'].copy()
            df_filtrado['status'] = np.where(df_filtrado[coluna_categoria_selecionada] == 'CHURN', 'Churn', 'Ativo')
            
            df_filtrado['ano_mes'] = df_historico_completo['data_snapshot'].dt.to_period('M')
            df_mensal = df_filtrado.loc[df_filtrado.groupby('ano_mes')['data_snapshot'].idxmax()]
            contagem_mensal = df_mensal.groupby(['ano_mes', 'status'])['cod_cliente'].count().unstack(fill_value=0)
            
            if 'Ativo' not in contagem_mensal.columns: contagem_mensal['Ativo'] = 0
            if 'Churn' not in contagem_mensal.columns: contagem_mensal['Churn'] = 0
            
            contagem_mensal['NET'] = contagem_mensal['Ativo'] - contagem_mensal['Churn']
            contagem_mensal.index = contagem_mensal.index.to_timestamp()
            
            st.subheader(f"Evolução Mensal do NET")
            st.line_chart(contagem_mensal, y='NET')
            
            with st.expander("Ver dados da tabela do gráfico"):
                st.dataframe(contagem_mensal)