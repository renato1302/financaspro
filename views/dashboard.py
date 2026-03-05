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

    # Resumo Financeiro
    ganhos = df_mes[df_mes['tipo'] == 'Ganho']['valor'].sum()
    gastos = abs(df_mes[df_mes['tipo'] == 'Gasto']['valor'].sum())

    st.title(f"📊 Dashboard {mes_sel}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Entradas", f"R$ {ganhos:,.2f}")
    c2.metric("Saídas", f"R$ {gastos:,.2f}", delta_color="inverse")
    c3.metric("Saldo", f"R$ {ganhos - gastos:,.2f}")

    st.divider()

    # Filtramos apenas os gastos para as análises gráficas
    df_gastos = df_mes[df_mes['tipo'] == 'Gasto'].copy()
    df_gastos['valor_abs'] = df_gastos['valor'].abs()

    if not df_gastos.empty:
        # --- SEÇÃO 1: ONDE ESTOU GASTANDO (CATEGORIAS) ---
        st.write("### 🔲 Mapa de Gastos (Categorias)")
        fig_tree = px.treemap(
            df_gastos,
            path=['grupo', 'subgrupo', 'subcategoria'],
            values='valor_abs',
            color='grupo',
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        st.plotly_chart(fig_tree, use_container_width=True)

        st.divider()

        # --- SEÇÃO 2: COMO ESTOU PAGANDO (CONTAS/CARTÕES) ---
        st.write("### 💳 Gastos por Conta / Cartão")

        # Agrupamento por conta
        df_contas_gasto = df_gastos.groupby('conta')['valor_abs'].sum().reset_index()
        df_contas_gasto = df_contas_gasto.sort_values(by='valor_abs', ascending=True)

        fig_contas = px.bar(
            df_contas_gasto,
            x='valor_abs',
            y='conta',
            orientation='h',
            text_auto='.2s',
            labels={'valor_abs': 'Total Gasto (R$)', 'conta': 'Conta/Cartão'},
            template="plotly_dark",
            color='conta',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )

        fig_contas.update_layout(showlegend=False)
        st.plotly_chart(fig_contas, use_container_width=True)

        st.divider()

        # --- SEÇÃO 3: TABELA DE DETALHES ---
        st.write("### 💡 Detalhamento de Oportunidades")
        rank = df_gastos.groupby(['conta', 'subgrupo', 'subcategoria'])['valor_abs'].sum().reset_index()
        st.dataframe(rank.sort_values(by='valor_abs', ascending=False), width='stretch', hide_index=True)
    else:
        st.write("Sem gastos registrados para este mês.")