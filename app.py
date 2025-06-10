# Em app.py
import streamlit as st
import pandas as pd
from datetime import datetime

# Importa as novas funções do nosso data_loader otimizado
from core.data_loader import get_available_snapshots, get_data_for_snapshot, get_net_history_as_df

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="B.blend RFV Tava -> Tá")
st.title("Análise de Migração RFV - B.blend")

# --- Carregamento dos Filtros ---
@st.cache_data(show_spinner="Carregando datas de análise disponíveis...")
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

    st.subheader("Filtros Gerais de Análise")
    modelo_rfv_map = {"Modelo Novo": "novo", "Modelo Antigo": "antigo"}
    modelo_rfv_label = st.selectbox("Escolha o Modelo RFV:", list(modelo_rfv_map.keys()))
    
    if modelo_rfv_label == "Modelo Novo":
        opcoes_foco_map = {"Geral": "categoria_geral_novo", "Cápsulas": "categoria_capsulas_novo", "Filtro": "categoria_filtro_novo", "Cilindros": "categoria_cilindro_novo"}
    else:
        opcoes_foco_map = {"Geral": "categoria_geral_antigo", "Cápsulas": "categoria_capsulas_antigo", "Insumos": "categoria_insumos_antigo"}

    tipo_rfv_foco_label = st.selectbox("Escolha o Tipo de RFV para Análise:", list(opcoes_foco_map.keys()))
    coluna_categoria_selecionada = opcoes_foco_map[tipo_rfv_foco_label]

# --- Criação das Abas ---
tab_matriz, tab_net = st.tabs(["Matriz de Migração", "Histórico de NET"])

# --- Conteúdo da Aba 1: Matriz de Migração ---
with tab_matriz:
    st.header("Análise de Migração 'Tava -> Tá'")
    st.markdown("Selecione os snapshots 'Tava' e 'Tá' para comparar a evolução dos clientes.")
    
    col_tava, col_ta = st.columns(2)
    with col_ta:
        opcao_ta_label = st.selectbox("Snapshot 'Tá':", options=list(opcoes_label_map.keys()), index=0, key="select_ta")
        data_ta_selecionada = opcoes_label_map[opcao_ta_label]
    
    with col_tava:
        opcoes_tava_disponiveis = {label: dt for label, dt in opcoes_label_map.items() if dt < data_ta_selecionada}
        data_tava_selecionada = None
        if opcoes_tava_disponiveis:
            opcao_tava_label = st.selectbox("Snapshot 'Tava':", options=list(opcoes_tava_disponiveis.keys()), index=0, key="select_tava")
            data_tava_selecionada = opcoes_tava_disponiveis[opcao_tava_label]
        else:
            st.warning("Não há snapshots anteriores para comparação.")

    if st.button("Processar Análise de Migração", key="btn_matriz"):
        if data_tava_selecionada:
            with st.spinner("Buscando dados e gerando matriz..."):
                df_tava = get_data_for_snapshot(data_tava_selecionada)
                df_ta = get_data_for_snapshot(data_ta_selecionada)

                if df_tava is not None and df_ta is not None:
                    # Lógica para gerar a matriz
                    df_tava_segmento = df_tava[['cod_cliente', coluna_categoria_selecionada]].rename(columns={coluna_categoria_selecionada: 'categoria'})
                    df_ta_segmento = df_ta[['cod_cliente', coluna_categoria_selecionada]].rename(columns={coluna_categoria_selecionada: 'categoria'})
                    df_merged = pd.merge(df_tava_segmento, df_ta_segmento, on='cod_cliente', how='outer', suffixes=('_tava', '_ta'))
                    df_merged['categoria_tava'].fillna('ENTRANTE NA BASE', inplace=True); df_merged['categoria_ta'].fillna('CHURN', inplace=True)
                    
                    # (Resto da lógica de ordenação e exibição das tabelas)
                    # ...
                    st.success("Matriz de migração gerada com sucesso!")

# --- Conteúdo da Aba 2: Histórico de NET ---
with tab_net:
    st.header("Histórico Mensal de NET (Clientes Ativos - Clientes em Churn)")
    st.info(f"O gráfico abaixo mostra a evolução do NET para a análise de '{tipo_rfv_foco_label}' do '{modelo_rfv_label}'. Clientes na categoria 'NOVO CLIENTE' são excluídos.")
    
    if st.button("Gerar Gráfico Histórico de NET", key="btn_net"):
        with st.spinner("Buscando e agregando dados no BigQuery..."):
            # Chama a nova função que faz o trabalho pesado no BQ
            df_grafico_net = get_net_history_as_df(coluna_categoria_selecionada)
        
        if not df_grafico_net.empty:
            st.subheader("Evolução Mensal do NET")
            st.line_chart(df_grafico_net, y='NET')
            
            with st.expander("Ver dados da tabela do gráfico"):
                st.dataframe(df_grafico_net)
        else:
            st.error("Não foi possível gerar os dados para o gráfico.")