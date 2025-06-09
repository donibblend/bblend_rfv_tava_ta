# Em app.py
import streamlit as st
import pandas as pd
from datetime import datetime

# Importa as novas funções do nosso data_loader
from core.data_loader import get_available_snapshots, get_data_for_snapshot

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="B.blend RFV Tava -> Tá")
st.title("Análise de Migração RFV - Tava -> Tá")

# --- Carregamento dos Filtros ---
# Agora carregamos apenas a lista de datas, o que é muito rápido.
@st.cache_data(show_spinner="Carregando datas de análise disponíveis...")
def carregar_opcoes_snapshot():
    return get_available_snapshots()

opcoes_snapshot_disponiveis = carregar_opcoes_snapshot()

if not opcoes_snapshot_disponiveis:
    st.error("Nenhuma data de snapshot encontrada na tabela de resumo do BigQuery. Verifique se o processo de backfill ou o agendamento rodaram com sucesso.")
    st.stop()

# --- Barra Lateral (Sidebar) ---
with st.sidebar:
    st.header("Filtros da Análise")
    
    # Mostra a data da última atualização
    st.caption(f"Dados atualizados pela última vez em: {opcoes_snapshot_disponiveis[0].strftime('%d/%m/%Y')}")
    
    # Cria as opções de label para o dropdown
    opcoes_label_map = {
        f"Semana {dt.isocalendar().week:02d} ({dt.strftime('%d/%m/%Y')})": dt 
        for dt in opcoes_snapshot_disponiveis
    }

    st.subheader("Data 'Tá' (Mais Recente)")
    opcao_ta_label = st.selectbox("Selecione o snapshot 'Tá':", options=list(opcoes_label_map.keys()), index=0)
    data_ta_selecionada = opcoes_label_map[opcao_ta_label]
    
    st.subheader("Data 'Tava' (Mais Antiga)")
    opcoes_tava_disponiveis = {label: dt for label, dt in opcoes_label_map.items() if dt < data_ta_selecionada}
    
    if opcoes_tava_disponiveis:
        opcao_tava_label = st.selectbox("Selecione o snapshot 'Tava':", options=list(opcoes_tava_disponiveis.keys()), index=0)
        data_tava_selecionada = opcoes_tava_disponiveis[opcao_tava_label]
    else:
        st.warning("Não há snapshots anteriores para comparação.")
        data_tava_selecionada = None

    modelo_rfv_map = {"Modelo Novo": "novo", "Modelo Antigo": "antigo"}
    modelo_rfv_label = st.selectbox("Escolha o Modelo RFV:", list(modelo_rfv_map.keys()))
    
    if modelo_rfv_label == "Modelo Novo":
        opcoes_foco_map = {"Geral": "categoria_geral", "Cápsulas": "categoria_capsulas", "Filtro": "categoria_filtro", "Cilindros": "categoria_cilindro"}
    else:
        st.warning("Modelo Antigo ainda não implementado nesta versão.")
        opcoes_foco_map = {}

    if opcoes_foco_map:
        tipo_rfv_foco_label = st.selectbox("Escolha o Tipo de RFV para Análise:", list(opcoes_foco_map.keys()))
        coluna_categoria_selecionada = opcoes_foco_map[tipo_rfv_foco_label]
    
    processar_btn = st.button("Processar Análise Tava/Tá")

# --- Lógica Principal ---
if processar_btn and data_tava_selecionada and opcoes_foco_map:
    with st.spinner(f"Buscando dados para os snapshots selecionados..."):
        # Busca apenas os dados necessários sob demanda
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
            
            # Lógica de ordenação e exibição das tabelas (continua a mesma)
            ORDER_Y = ['DIAMANTE', 'OURO', 'PRATA', 'BRONZE', 'NOVO CLIENTE', 'CHURN', 'ENTRANTE NA BASE']
            ORDER_X = ['CHURN', 'NOVO CLIENTE', 'BRONZE', 'PRATA', 'OURO', 'DIAMANTE']
            
            tabela_base = pd.crosstab(df_merged['categoria_tava'], df_merged['categoria_ta'])
            present_y = tabela_base.index.tolist(); present_x = tabela_base.columns.tolist()
            final_order_y = [cat for cat in ORDER_Y if cat in present_y] + sorted([cat for cat in present_y if cat not in ORDER_Y])
            final_order_x = [cat for cat in ORDER_X if cat in present_x] + sorted([cat for cat in present_x if cat not in ORDER_X])
            tabela_reordenada = tabela_base.reindex(index=final_order_y, columns=final_order_x, fill_value=0)
            tabela_absoluta = tabela_reordenada.copy()
            tabela_absoluta.loc['Total',:] = tabela_absoluta.sum(axis=0).astype(int)
            tabela_absoluta['Total'] = tabela_absoluta.sum(axis=1).astype(int)
            tabela_percentual = tabela_reordenada.div(tabela_reordenada.sum(axis=1), axis=0).fillna(0) * 100
            
            st.header(f"Matriz de Migração - {modelo_rfv_label} ({tipo_rfv_foco_label})")
            st.markdown(f"Análise comparando a base de clientes em **{data_tava_selecionada.strftime('%d/%m/%Y')} (Tava)** com **{data_ta_selecionada.strftime('%d/%m/%Y')} (Tá)**.")
            st.subheader("Visão em Números Absolutos")
            st.dataframe(tabela_absoluta.style.format(lambda x: f"{x:,.0f}".replace(",", ".")).background_gradient(cmap='viridis_r'))
            st.subheader("Visão em Percentual (%)")
            st.dataframe(tabela_percentual.style.format('{:.2f}%').background_gradient(cmap='viridis_r'))

elif not processar_btn:
    st.info("Por favor, selecione os filtros na barra lateral e clique em 'Processar Análise' para ver os resultados.")