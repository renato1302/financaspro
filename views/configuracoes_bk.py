import streamlit as st
import pandas as pd
from database import executar_query, ler_dados

def render_configuracoes():
    if st.session_state.get('role') != 'Administrador':
        st.error("🚫 Acesso negado. Apenas administradores podem acessar esta página.")
        return

    st.header("⚙️ Configurações de Cadastro")
    tab_contas, tab_cats = st.tabs(["💳 Contas e Cartões", "📁 Hierarquia de Categorias"])

    with tab_contas:
        st.subheader("Nova Conta")
        with st.form("form_conta", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            nome_c = c1.text_input("Nome da Conta")
            tipo_c = c2.selectbox("Tipo", ["Conta Corrente", "Cartão", "Dinheiro"])
            venc = c3.text_input("Vencimento (Ex: dia 05)")
            if st.form_submit_button("Salvar Conta"):
                if nome_c:
                    executar_query("INSERT INTO cad_contas VALUES (?, ?, ?)", (nome_c.strip(), tipo_c, venc))
                    st.success("Conta adicionada com sucesso!")
                    st.rerun()
                else:
                    st.error("O nome da conta é obrigatório.")

        st.divider()

        st.subheader("Contas Cadastradas")
        df_contas = ler_dados("cad_contas")
        st.dataframe(df_contas, width='stretch', hide_index=True)

        if not df_contas.empty:
            with st.expander("✏️ Editar ou 🗑️ Excluir Conta"):
                conta_sel = st.selectbox("Selecione a Conta para Modificar", df_contas['nome'].tolist(),
                                         key="conta_sel_edit")
                if conta_sel:
                    row_conta = df_contas[df_contas['nome'] == conta_sel].iloc[0]
                    with st.form("form_edit_conta"):
                        c1, c2, c3 = st.columns(3)
                        novo_nome = c1.text_input("Nome da Conta", value=row_conta['nome'])

                        tipos_conta = ["Conta Corrente", "Cartão", "Dinheiro"]
                        idx_tipo = tipos_conta.index(row_conta['tipo']) if row_conta['tipo'] in tipos_conta else 0
                        novo_tipo = c2.selectbox("Tipo", tipos_conta, index=idx_tipo)

                        venc_val = str(row_conta['vencimento']) if not pd.isna(row_conta['vencimento']) else ""
                        novo_venc = c3.text_input("Vencimento", value=venc_val)

                        col_btn1, col_btn2 = st.columns(2)
                        if col_btn1.form_submit_button("💾 Salvar Alterações"):
                            if novo_nome:
                                executar_query("UPDATE cad_contas SET nome=?, tipo=?, vencimento=? WHERE nome=?",
                                               (novo_nome.strip(), novo_tipo, novo_venc, row_conta['nome']))
                                if novo_nome.strip() != row_conta['nome']:
                                    executar_query("UPDATE transacoes SET conta=? WHERE conta=?",
                                                   (novo_nome.strip(), row_conta['nome']))
                                st.success("Conta atualizada!")
                                st.rerun()

                        if col_btn2.form_submit_button("🗑️ Excluir Conta"):
                            executar_query("DELETE FROM cad_contas WHERE nome=?", (row_conta['nome'],))
                            st.success("Conta excluída!")
                            st.rerun()

    with tab_cats:
        st.subheader("Cadastrar Nova Divisão")
        with st.form("form_hierarquia", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            g = col1.text_input("Grupo (Ex: Casa)")
            sg = col2.text_input("Subgrupo (Ex: Mercado)")
            sc = col3.text_input("Sub-Categoria (Ex: Limpeza)")

            if st.form_submit_button("Adicionar Estrutura"):
                if g and sg and sc:
                    executar_query("INSERT OR IGNORE INTO cad_categorias VALUES (?, ?, ?)",
                                   (g.strip(), sg.strip(), sc.strip()))
                    st.success("Estrutura adicionada!")
                    st.rerun()
                else:
                    st.error("Preencha todos os campos.")

        st.divider()

        df_cat = ler_dados("cad_categorias")
        if not df_cat.empty:
            st.subheader("Estrutura Atual")
            st.dataframe(df_cat.sort_values(['grupo', 'subgrupo']), width='stretch', hide_index=True)

            with st.expander("✏️ Editar ou 🗑️ Excluir Categoria"):
                df_cat['nome_completo'] = df_cat['grupo'] + " > " + df_cat['subgrupo'] + " > " + df_cat['subcategoria']
                cat_sel = st.selectbox("Selecione a Categoria", df_cat['nome_completo'].tolist(), key="cat_sel_edit")

                if cat_sel:
                    row_c = df_cat[df_cat['nome_completo'] == cat_sel].iloc[0]

                    with st.form("form_edit_cat"):
                        c1, c2, c3 = st.columns(3)
                        novo_g = c1.text_input("Grupo", value=row_c['grupo'])
                        novo_sg = c2.text_input("Subgrupo", value=row_c['subgrupo'])
                        novo_sc = c3.text_input("Sub-Categoria", value=row_c['subcategoria'])

                        col_btn1, col_btn2 = st.columns(2)
                        if col_btn1.form_submit_button("💾 Salvar Alterações"):
                            if novo_g and novo_sg and novo_sc:
                                executar_query("""
                                    UPDATE cad_categorias
                                    SET grupo=?, subgrupo=?, subcategoria=?
                                    WHERE grupo=? AND subgrupo=? AND subcategoria=?
                                """, (novo_g.strip(), novo_sg.strip(), novo_sc.strip(), row_c['grupo'],
                                      row_c['subgrupo'], row_c['subcategoria']))

                                executar_query("""
                                    UPDATE transacoes
                                    SET grupo=?, subgrupo=?, subcategoria=?
                                    WHERE grupo=? AND subgrupo=? AND subcategoria=?
                                """, (novo_g.strip(), novo_sg.strip(), novo_sc.strip(), row_c['grupo'],
                                      row_c['subgrupo'], row_c['subcategoria']))

                                st.success("Categoria atualizada em todo o sistema!")
                                st.rerun()

                        if col_btn2.form_submit_button("🗑️ Excluir Categoria"):
                            executar_query("""
                                DELETE FROM cad_categorias
                                WHERE grupo=? AND subgrupo=? AND subcategoria=?
                            """, (row_c['grupo'], row_c['subgrupo'], row_c['subcategoria']))
                            st.success("Categoria excluída!")
                            st.rerun()

            st.divider()
            if st.button("🗑️ Limpar todas as categorias", type="secondary"):
                executar_query("DELETE FROM cad_categorias")
                st.success("Todas as categorias foram removidas.")
                st.rerun()