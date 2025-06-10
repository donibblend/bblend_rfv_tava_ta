# Em app.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Importa as novas funções do nosso data_loader
from core.data_loader import get_available_snapshots, get_data_for_snapshot

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="B.blend RFV Tava -> Tá")
st.title("Análise de Migração RFV - Tava -> Tá")

# --- Carregamento dos Filtros ---
@st.cache_data(show_spinner="Carregando histórico de RFV do BigQuery...")
def carregar_opcoes_snapshot():
    return get_available_snapshots()

opcoes_snapshot_disponiveis = carregar_opcoes_snapshot()

if not opcoes_snapshot_disponiveis:
    st.error("Nenhuma data de snapshot encontrada na tabela de resumo do BigQuery.")
    st.stop()

# --- Barra Lateral (Sidebar) ---
with st.sidebar:
    st.header("Filtros da Análise")
    
    st.caption(f"Dados atualizados pela última vez em: {opcoes_snapshot_disponiveis[0].strftime('%d/%m/%Y')}")
    
    opcoes_label_map = {
        f"Semana {dt.isocalendar().week:02d} ({dt.strftime('%d/%m/%Y')})": dt 
        for dt in opcoes_snapshot_disponiveis
    }

    # Filtros para a Matriz de Migração
    st.subheader("Filtros para Matriz 'Tava -> Tá'")
    opcao_ta_label = st.selectbox("Selecione o snapshot 'Tá':", options=list(opcoes_label_map.keys()), index=0)
    data_ta_selecionada = opcoes_label_map[opcao_ta_label]
    
    opcoes_tava_disponiveis = {label: dt for label, dt in opcoes_label_map.items() if dt < data_ta_selecionada}
    
    data_tava_selecionada = None
    if opcoes_tava_disponiveis:
        opcao_tava_label = st.selectbox("Selecione o snapshot 'Tava':", options=list(opcoes_tava_disponiveis.keys()), index=0)
        data_tava_selecionada = opcoes_tava_disponiveis[opcao_tava_label]
    else:
        st.warning("Não há snapshots 'Tava' anteriores para comparação.")

    # Filtros Gerais (usados por ambas as abas)
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
    processar_matriz_btn = st.button("Processar Análise de Migração", key="btn_matriz")
    
    if processar_matriz_btn:
        if data_tava_selecionada:
            with st.spinner(f"Buscando dados para os snapshots selecionados..."):
                df_tava = get_data_for_snapshot(data_tava_selecionada)
                df_ta = get_data_for_snapshot(data_ta_selecionada)

            if df_tava is None or df_ta is None:
                st.error("Não foi possível buscar os dados para uma ou ambas as datas selecionadas.")
            else:
                with st.spinner("Gerando matriz de migração..."):
                    df_tava_segmento = df_tava[['cod_cliente', coluna_categoria_selecionada]].rename(columns={coluna_categoria_selecionada: 'categoria'})
                    df_ta_segmento = df_ta[['cod_cliente', coluna_categoria_selecionada]].rename(columns={coluna_categoria_selecionada: 'categoria'})
                    
                    df_merged = pd.merge(df_tava_segmento, df_ta_segmento, on='cod_cliente', how='outer', suffixes=('_tava', '_ta'))
                    df_merged['categoria_tava'].fillna('ENTRANTE NA BASE', inplace=True)
                    df_merged['categoria_ta'].fillna('CHURN', inplace=True)
                    
                    if modelo_rfv_label == 'Modelo Novo':
                        ORDER_Y = ['DIAMANTE', 'OURO', 'PRATA', 'BRONZE', 'NOVO CLIENTE', 'CHURN', 'ENTRANTE NA BASE']
                        ORDER_X = ['CHURN', 'NOVO CLIENTE', 'BRONZE', 'PRATA', 'OURO', 'DIAMANTE']
                    else:
                        ORDER_Y = ['ELITE', 'POTENCIAL ELITE', 'CLIENTE LEAL', 'PROMISSOR', 'PEGANDO NO SONO', 'EM RISCO', 'ADORMECIDO', 'NOVO CLIENTE', 'CHURN', 'ENTRANTE NA BASE']
                        ORDER_X = ['CHURN', 'NOVO CLIENTE', 'ADORMECIDO', 'EM RISCO', 'PEGANDO NO SONO', 'PROMISSOR', 'CLIENTE LEAL', 'POTENCIAL ELITE', 'ELITE']
                    
                    st.header(f"Matriz de Migração - {modelo_rfv_label} ({tipo_rfv_foco_label})")
                    st.markdown(f"Análise comparando a base de clientes em **{data_tava_selecionada.strftime('%d/%m/%Y')} (Tava)** com **{data_ta_selecionada.strftime('%d/%m/%Y')} (Tá)**.")
                    
                    tabela_base = pd.crosstab(df_merged['categoria_tava'], df_merged['categoria_ta'])
                    present_y = tabela_base.index.tolist(); present_x = tabela_base.columns.tolist()
                    final_order_y = [cat for cat in ORDER_Y if cat in present_y] + sorted([cat for cat in present_y if cat not in ORDER_Y])
                    final_order_x = [cat for cat in ORDER_X if cat in present_x] + sorted([cat for cat in present_x if cat not in ORDER_X])
                    tabela_reordenada = tabela_base.reindex(index=final_order_y, columns=final_order_x, fill_value=0)
                    tabela_absoluta = tabela_reordenada.copy()
                    tabela_absoluta.loc['Total',:] = tabela_absoluta.sum(axis=0).astype(int)
                    tabela_absoluta['Total'] = tabela_absoluta.sum(axis=1).astype(int)
                    tabela_percentual = tabela_reordenada.div(tabela_reordenada.sum(axis=1), axis=0).fillna(0) * 100
                    
                    st.subheader("Visão em Números Absolutos")
                    st.dataframe(tabela_absoluta.style.format(lambda x: f"{x:,.0f}".replace(",", ".")).background_gradient(cmap='viridis_r'))
                    st.subheader("Visão em Percentual (%)")
                    st.dataframe(tabela_percentual.style.format('{:.2f}%').background_gradient(cmap='viridis_r'))
        else:
            st.warning("Por favor, selecione um período 'Tava' válido para gerar a matriz.")
    else:
        st.info("Selecione os filtros na barra lateral e clique em 'Processar Análise de Migração' para ver a matriz.")


# --- Conteúdo da Aba 2: Histórico de NET ---
with tab_net:
    st.header("Histórico Mensal de NET (Clientes Ativos - Clientes em Churn)")
    st.info(f"O gráfico abaixo mostra a evolução do NET para a análise de '{tipo_rfv_foco_label}' do '{modelo_rfv_label}'. Clientes na categoria 'NOVO CLIENTE' são excluídos deste cálculo.")
    
    with st.spinner("Calculando histórico de NET..."):
        # Cria uma cópia para não modificar o dataframe original em cache
        df_net_calc = df_historico_completo.copy()
        
        # 1. Filtra para não incluir 'NOVO CLIENTE' na conta
        df_filtrado = df_net_calc[df_net_calc[coluna_categoria_selecionada] != 'NOVO CLIENTE'].copy()
        
        # 2. Define o status 'Ativo' ou 'Churn'
        df_filtrado['status'] = np.where(df_filtrado[coluna_categoria_selecionada] == 'CHURN', 'Churn', 'Ativo')
        
        # 3. Agrega por mês, pegando o último snapshot de cada mês para a análise
        df_filtrado['ano_mes'] = df_filtrado['data_snapshot'].dt.to_period('M')
        # idxmax() encontra o índice da maior data (a mais recente) para cada grupo de ano/mês
        df_mensal = df_filtrado.loc[df_filtrado.groupby('ano_mes')['data_snapshot'].idxmax()]

        # 4. Conta quantos clientes estão em cada status por mês
        contagem_mensal = df_mensal.groupby(['ano_mes', 'status'])['cod_cliente'].count().unstack(fill_value=0)
        
        # Garante que as colunas 'Ativo' e 'Churn' sempre existam, mesmo que não haja clientes em uma delas
        if 'Ativo' not in contagem_mensal.columns: contagem_mensal['Ativo'] = 0
        if 'Churn' not in contagem_mensal.columns: contagem_mensal['Churn'] = 0
        
        # 5. Calcula a métrica NET
        contagem_mensal['NET'] = contagem_mensal['Ativo'] - contagem_mensal['Churn']
        
        # Converte o índice de 'Período' para 'Timestamp' para o gráfico
        contagem_mensal.index = contagem_mensal.index.to_timestamp()
        
        # 6. Exibe o gráfico de linha
        st.subheader(f"Evolução Mensal do NET")
        st.line_chart(contagem_mensal, y='NET')
        
        # 7. Exibe a tabela de dados com um expander
        with st.expander("Ver dados da tabela do gráfico"):
            st.dataframe(contagem_mensal)