import streamlit as st
import plotly.express as px
import pandas as pd
from database import carregar_dados


def render_dashboard():
    df = carregar_dados()
    if df.empty:
        st.info("Aguardando lançamentos para gerar análise...")
        return

    # Filtro de Período
    df['mes_ano'] = df['data'].dt.strftime('%m/%Y')
    mes_sel = st.sidebar.selectbox("Mês", sorted(df['mes_ano'].unique(), reverse=True))
    df_mes = df[df['mes_ano'] == mes_sel].copy()

    # Resumo
    ganhos = df_mes[df_mes['tipo'] == 'Ganho']['valor'].sum()
    gastos = abs(df_mes[df_mes['tipo'] == 'Gasto']['valor'].sum())

    st.title(f"📊 Dashboard {mes_sel}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Entradas", f"R$ {ganhos:,.2f}")
    c2.metric("Saídas", f"R$ {gastos:,.2f}", delta_color="inverse")
    c3.metric("Saldo", f"R$ {ganhos - gastos:,.2f}")

    st.divider()

    # Gráfico Hierárquico
    st.write("### 🔲 Mapa de Gastos (Grupo > Subgrupo > Sub-Categoria)")
    df_gastos = df_mes[df_mes['tipo'] == 'Gasto'].copy()
    df_gastos['valor_abs'] = df_gastos['valor'].abs()

    if not df_gastos.empty:
        fig = px.treemap(
            df_gastos,
            path=['grupo', 'subgrupo', 'subcategoria'],
            values='valor_abs',
            color='grupo',
            template="plotly_dark"
        )
        st.plotly_chart(fig, width='stretch')

        # Análise de Oportunidade de Economia
        st.write("### 💡 Onde você mais gastou neste mês?")
        rank = df_gastos.groupby(['subgrupo', 'subcategoria'])['valor_abs'].sum().reset_index()
        st.dataframe(rank.sort_values(by='valor_abs', ascending=False), width='stretch')
    else:
        st.write("Sem gastos para exibir.")