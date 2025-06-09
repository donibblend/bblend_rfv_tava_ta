# Em app.py

import streamlit as st
import pandas as pd
from datetime import datetime

# A única função que precisamos agora é a que carrega os dados já processados
from core.data_loader import carregar_dados

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="B.blend RFV Tava -> Tá")
st.title("Análise de Migração RFV - Tava -> Tá")

# --- Carregamento dos Dados Históricos ---
@st.cache_data(show_spinner="Carregando histórico de RFV do BigQuery...")
def carregar_dados_completos():
    df = carregar_dados()
    if df is not None and not df.empty:
        # Ordena os snapshots para que os filtros apareçam na ordem correta
        df.sort_values(by='data_snapshot', ascending=False, inplace=True)
    return df

df_historico_completo = carregar_dados_completos()

if df_historico_completo is None or df_historico_completo.empty:
    st.error("Falha ao carregar o histórico de RFV do BigQuery ou a tabela está vazia.")
    st.stop()

# --- Lógica dos Novos Filtros e UI ---
st.sidebar.header("Filtros da Análise")

# Pega a data da última atualização para mostrar ao usuário
ultima_atualizacao = df_historico_completo['data_snapshot'].max()
st.sidebar.caption(f"Dados atualizados pela última vez em: {ultima_atualizacao.strftime('%d/%m/%Y')}")

# Cria colunas de Ano, Mês e Semana para os filtros
df_historico_completo['ano'] = df_historico_completo['data_snapshot'].dt.year
df_historico_completo['mes'] = df_historico_completo['data_snapshot'].dt.month
df_historico_completo['semana_do_ano'] = df_historico_completo['data_snapshot'].dt.isocalendar().week

# Cria uma lista de opções para os filtros dropdown
opcoes_snapshot = df_historico_completo[['data_snapshot', 'ano', 'mes', 'semana_do_ano']].drop_duplicates()
opcoes_snapshot['label'] = opcoes_snapshot.apply(
    lambda row: f"Ano: {row['ano']} - Mês: {row['mes']:02d} - (Semana {row['semana_do_ano']:02d}) -> {row['data_snapshot'].strftime('%d/%m/%Y')}",
    axis=1
)

# Filtros para "Tá"
st.sidebar.subheader("Data 'Tá' (Mais Recente)")
opcao_ta_label = st.sidebar.selectbox("Selecione o snapshot 'Tá':", options=opcoes_snapshot['label'], index=0)
data_ta_selecionada = opcoes_snapshot[opcoes_snapshot['label'] == opcao_ta_label]['data_snapshot'].iloc[0]

# Filtros para "Tava"
st.sidebar.subheader("Data 'Tava' (Mais Antiga)")
# Garante que as opções para "Tava" sejam sempre anteriores à data "Tá" selecionada
opcoes_tava = opcoes_snapshot[opcoes_snapshot['data_snapshot'] < data_ta_selecionada]
if not opcoes_tava.empty:
    opcao_tava_label = st.sidebar.selectbox("Selecione o snapshot 'Tava':", options=opcoes_tava['label'], index=0)
    data_tava_selecionada = opcoes_tava[opcoes_tava['label'] == opcao_tava_label]['data_snapshot'].iloc[0]
else:
    st.sidebar.warning("Não há snapshots anteriores disponíveis para comparação.")
    data_tava_selecionada = None

modelo_rfv_map = {"Modelo Novo (Diamante, Ouro...)": "novo", "Modelo Antigo (Elite, Potencial Elite...)": "antigo"}
modelo_rfv_label = st.sidebar.selectbox("Escolha o Modelo RFV:", list(modelo_rfv_map.keys()))
modelo_rfv_escolhido = modelo_rfv_map[modelo_rfv_label]

if modelo_rfv_escolhido == 'novo':
    opcoes_foco_map = {"Geral": "categoria_geral", "Cápsulas": "categoria_capsulas", "Filtro": "categoria_filtro", "Cilindros": "categoria_cilindro"}
else:
    opcoes_foco_map = {"Geral": "categoria_geral", "Cápsulas": "categoria_capsulas", "Insumos": "categoria_insumos"} # Ajuste se necessário

tipo_rfv_foco_label = st.sidebar.selectbox("Escolha o Tipo de RFV para Análise:", list(opcoes_foco_map.keys()))
coluna_categoria_selecionada = opcoes_foco_map[tipo_rfv_foco_label]

processar_btn = st.sidebar.button("Processar Análise Tava/Tá")

# --- Lógica Principal e Exibição de Resultados (Agora muito mais simples!) ---
if processar_btn and data_tava_selecionada:
    
    # Filtra os dados para a data 'Tava'
    df_tava = df_historico_completo[df_historico_completo['data_snapshot'] == data_tava_selecionada]
    
    # Filtra os dados para a data 'Tá'
    df_ta = df_historico_completo[df_historico_completo['data_snapshot'] == data_ta_selecionada]
    
    # Renomeia a coluna de categoria selecionada para 'categoria' para o merge
    df_tava = df_tava[['cod_cliente', coluna_categoria_selecionada]].rename(columns={coluna_categoria_selecionada: 'categoria'})
    df_ta = df_ta[['cod_cliente', coluna_categoria_selecionada]].rename(columns={coluna_categoria_selecionada: 'categoria'})

    df_merged = pd.merge(df_tava, df_ta, on='cod_cliente', how='outer', suffixes=('_tava', '_ta'))
    df_merged['categoria_tava'].fillna('ENTRANTE NA BASE', inplace=True)
    df_merged['categoria_ta'].fillna('CHURN', inplace=True)
    
    # (Lógica para ordenar e gerar as tabelas continua a mesma)
    if modelo_rfv_escolhido == 'novo':
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
    tabela_percentual = tabela_reordenada.div(tabela_reordenada.sum(axis=1), axis=0) * 100
    
    st.subheader("Visão em Números Absolutos")
    st.dataframe(tabela_absoluta.style.format(lambda x: f"{x:,.0f}".replace(",", ".")).background_gradient(cmap='viridis_r'))
    st.subheader("Visão em Percentual (%)")
    st.dataframe(tabela_percentual.style.format('{:.2f}%').background_gradient(cmap='viridis_r'))

elif not processar_btn:
    st.info("Por favor, selecione os filtros na barra lateral e clique em 'Processar Análise' para ver os resultados.")
else:
    # Caso onde a data 'Tava' não pode ser selecionada
    st.error("Não foi possível gerar a análise. Verifique se há um período 'Tava' válido para a data 'Tá' selecionada.")