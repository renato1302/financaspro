import streamlit as st
import pandas as pd
from database import executar_query, ler_dados


def render_lancamentos():
    st.header("📝 Gestão de Lançamentos")

    df_contas = ler_dados("cad_contas")
    df_cats = ler_dados("cad_categorias")

    if df_contas.empty or df_cats.empty:
        st.warning("⚠️ O Administrador precisa cadastrar Contas e Hierarquia de Categorias nas Configurações primeiro.")
        return

    pode_editar = st.session_state.get('role') in ["Administrador", "Consegue Ler e Lançamentos"]

    # Exibe o form de cadastro apenas se tiver permissão
    if pode_editar:
        with st.expander("➕ Novo Lançamento Detalhado", expanded=True):
            st.markdown("### 1. Classificação")
            c1, c2, c3 = st.columns(3)

            with c1:
                grupo_sel = st.selectbox("Grupo", sorted(df_cats['grupo'].unique()))
            with c2:
                sub_opts = df_cats[df_cats['grupo'] == grupo_sel]['subgrupo'].unique()
                subgrupo_sel = st.selectbox("Subgrupo", sorted(sub_opts))
            with c3:
                subcat_opts = df_cats[(df_cats['grupo'] == grupo_sel) &
                                      (df_cats['subgrupo'] == subgrupo_sel)]['subcategoria'].unique()
                subcat_sel = st.selectbox("Sub-Categoria", sorted(subcat_opts))

            st.markdown("### 2. Detalhes Financeiros")
            with st.form("form_registro", clear_on_submit=True):
                col_v, col_t, col_c = st.columns(3)
                valor = col_v.number_input("Valor (R$)", min_value=0.0, format="%.2f")
                tipo = col_t.radio("Tipo", ["Gasto", "Ganho"], horizontal=True)
                conta = col_c.selectbox("Conta", df_contas['nome'].unique())

                data = st.date_input("Data")
                descricao = st.text_input("Descrição (Ex: Compras semanais)")

                if st.form_submit_button("Confirmar Lançamento"):
                    if valor > 0:
                        valor_f = -valor if tipo == "Gasto" else valor
                        executar_query("""
                            INSERT INTO transacoes (valor, tipo, grupo, subgrupo, subcategoria, conta, data, pago, recorrente, descricao)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (valor_f, tipo, grupo_sel, subgrupo_sel, subcat_sel, conta, data, True, False, descricao))
                        st.success("Lançamento realizado!")
                        st.rerun()
                    else:
                        st.error("O valor deve ser maior que zero.")
        st.divider()
    else:
        st.info("🔒 Seu nível de acesso permite apenas visualização dos lançamentos.")

    # Visualização da Tabela
    st.subheader("📋 Histórico")
    df_trans = ler_dados("transacoes")

    if not df_trans.empty:
        df_view = df_trans[['id', 'data', 'descricao', 'valor', 'tipo', 'conta', 'grupo', 'subcategoria']].sort_values(
            'data', ascending=False)
        st.dataframe(df_view, width='stretch', hide_index=True)

        # Exibe edição/exclusão apenas se tiver permissão
        if pode_editar:
            with st.expander("✏️ Editar ou 🗑️ Excluir Lançamento Existente"):
                df_trans['label'] = df_trans['id'].astype(str) + " | " + df_trans['data'].astype(str) + " | " + \
                                    df_trans['descricao'] + " | R$ " + df_trans['valor'].astype(str)
                trans_sel_label = st.selectbox("Selecione o Lançamento para Alterar", df_trans['label'].tolist(),
                                               key="sel_trans_edit")

                if trans_sel_label:
                    trans_id = int(trans_sel_label.split(" | ")[0])
                    row = df_trans[df_trans['id'] == trans_id].iloc[0]

                    st.markdown("#### Alterar Dados do Lançamento")

                    grupos = sorted(df_cats['grupo'].unique())
                    default_g = row['grupo'] if row['grupo'] in grupos else (grupos[0] if grupos else None)
                    edit_g = st.selectbox("Grupo", grupos, index=grupos.index(default_g) if default_g else 0,
                                          key="ed_g")

                    subgrupos = sorted(df_cats[df_cats['grupo'] == edit_g]['subgrupo'].unique())
                    default_sg = row['subgrupo'] if row['subgrupo'] in subgrupos else (
                        subgrupos[0] if subgrupos else None)
                    edit_sg = st.selectbox("Subgrupo", subgrupos,
                                           index=subgrupos.index(default_sg) if default_sg else 0, key="ed_sg")

                    subcats = sorted(df_cats[(df_cats['grupo'] == edit_g) & (df_cats['subgrupo'] == edit_sg)][
                                         'subcategoria'].unique())
                    default_sc = row['subcategoria'] if row['subcategoria'] in subcats else (
                        subcats[0] if subcats else None)
                    edit_sc = st.selectbox("Sub-Categoria", subcats,
                                           index=subcats.index(default_sc) if default_sc else 0, key="ed_sc")

                    col_v, col_t, col_c = st.columns(3)
                    val_absoluto = abs(float(row['valor']))
                    edit_val = col_v.number_input("Valor (R$)", min_value=0.0, format="%.2f", value=val_absoluto,
                                                  key="ed_val")
                    edit_tipo = col_t.radio("Tipo", ["Gasto", "Ganho"], horizontal=True,
                                            index=0 if row['tipo'] == "Gasto" else 1, key="ed_tipo")

                    contas_list = df_contas['nome'].unique().tolist()
                    edit_conta = col_c.selectbox("Conta", contas_list, index=contas_list.index(row['conta']) if row[
                                                                                                                    'conta'] in contas_list else 0,
                                                 key="ed_conta")

                    try:
                        data_val = pd.to_datetime(row['data']).date()
                    except:
                        data_val = pd.to_datetime('today').date()

                    col_d, col_desc = st.columns([1, 2])
                    edit_data = col_d.date_input("Data", value=data_val, key="ed_data")
                    edit_desc = col_desc.text_input("Descrição", value=row['descricao'], key="ed_desc")

                    col_btn1, col_btn2 = st.columns(2)
                    if col_btn1.button("💾 Atualizar Lançamento", type="primary"):
                        if edit_val > 0:
                            valor_f = -edit_val if edit_tipo == "Gasto" else edit_val
                            executar_query("""
                                UPDATE transacoes
                                SET valor=?, tipo=?, grupo=?, subgrupo=?, subcategoria=?, conta=?, data=?, descricao=?
                                WHERE id=?
                            """, (valor_f, edit_tipo, edit_g, edit_sg, edit_sc, edit_conta, edit_data, edit_desc,
                                  trans_id))
                            st.success("Lançamento atualizado com sucesso!")
                            st.rerun()
                        else:
                            st.error("O valor deve ser maior que zero.")

                    if col_btn2.button("🗑️ Excluir Lançamento"):
                        executar_query("DELETE FROM transacoes WHERE id=?", (trans_id,))
                        st.success("Lançamento apagado!")
                        st.rerun()
    else:
        st.info("Nenhum lançamento registrado ainda.")