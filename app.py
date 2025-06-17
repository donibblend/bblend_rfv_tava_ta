# Em app.py (VERSÃO DE DEPURAÇÃO)
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import altair as alt

from core.data_loader import get_available_snapshots, get_data_for_snapshot, get_net_history_as_df

st.set_page_config(layout="wide", page_title="B.blend RFV Tava -> Tá")
st.title("Análise de Migração RFV - B.blend (MODO DE DEPURAÇÃO)")

st.warning("ESTA É A VERSÃO DE TESTE DE DEPURAÇÃO - v11")

opcoes_snapshot_disponiveis = get_available_snapshots()

# Verifica se o carregamento inicial de datas deu erro
if isinstance(opcoes_snapshot_disponiveis, Exception):
    st.error("Erro Crítico ao Carregar a Lista de Datas do BigQuery:")
    st.exception(opcoes_snapshot_disponiveis)
    st.stop()

if not opcoes_snapshot_disponiveis:
    st.error("Nenhuma data de snapshot encontrada.")
    st.stop()

with st.sidebar:
    # (A barra lateral continua a mesma)
    st.header("Filtros da Análise")
    st.caption(f"Dados atualizados pela última vez em: {opcoes_snapshot_disponiveis[0].strftime('%d/%m/%Y')}")
    opcoes_label_map = { f"Semana {dt.isocalendar().week:02d} ({dt.strftime('%d/%m/%Y')})": dt for dt in opcoes_snapshot_disponiveis }
    st.subheader("Filtros Gerais de Análise")
    modelo_rfv_map = {"Modelo Novo": "novo", "Modelo Antigo": "antigo"}
    modelo_rfv_label = st.selectbox("Escolha o Modelo RFV:", list(modelo_rfv_map.keys()))
    if modelo_rfv_label == "Modelo Novo":
        opcoes_foco_map = {"Geral": "categoria_geral_novo", "Cápsulas": "categoria_capsulas_novo", "Filtro": "categoria_filtro_novo", "Cilindros": "categoria_cilindro_novo"}
    else:
        opcoes_foco_map = {"Geral": "categoria_geral_antigo", "Cápsulas": "categoria_capsulas_antigo", "Insumos": "categoria_insumos_antigo"}
    tipo_rfv_foco_label = st.selectbox("Escolha o Tipo de RFV para Análise:", list(opcoes_foco_map.keys()))
    coluna_categoria_selecionada = opcoes_foco_map[tipo_rfv_foco_label]

tab_matriz, tab_net = st.tabs(["Matriz de Migração", "Histórico de Atividade"])

with tab_matriz:
    st.header("Análise de Migração 'Tava -> Tá'")
    st.markdown("Selecione os snapshots 'Tava' e 'Tá' abaixo para comparar.")
    
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
            with st.spinner("Buscando dados..."):
                df_tava = get_data_for_snapshot(data_tava_selecionada)
                df_ta = get_data_for_snapshot(data_ta_selecionada)
            
            # --- NOVA VERIFICAÇÃO DE ERRO ---
            is_error = False
            if isinstance(df_tava, Exception):
                st.error("Erro ao buscar dados 'Tava':")
                st.exception(df_tava)
                is_error = True
            if isinstance(df_ta, Exception):
                st.error("Erro ao buscar dados 'Tá':")
                st.exception(df_ta)
                is_error = True

            if not is_error:
                # Se não houve erro, continua com a lógica normal
                with st.spinner("Gerando matriz de migração..."):
                    # (A lógica de gerar a matriz continua a mesma)
                    st.success("Lógica da matriz executada (código omitido para brevidade)")

with tab_net:
    st.header("Histórico Mensal da Taxa de Ativos")
    st.info(f"O gráfico abaixo mostra a evolução da Taxa de Ativos (%) para a análise de '{tipo_rfv_foco_label}'.")
    
    if st.button("Gerar Gráfico Histórico", key="btn_net"):
        with st.spinner("Buscando e agregando dados no BigQuery..."):
            df_grafico = get_net_history_as_df(coluna_categoria_selecionada)
        
        # --- NOVA VERIFICAÇÃO DE ERRO ---
        if isinstance(df_grafico, Exception):
            st.error("Erro ao gerar dados do gráfico:")
            st.exception(df_grafico)
        elif not df_grafico.empty:
            # Se não houve erro, continua
            st.success("Lógica do gráfico executada (código omitido para brevidade)")