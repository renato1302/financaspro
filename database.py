import duckdb
import pandas as pd
import hashlib


def hash_password(password):
    """Gera um hash SHA-256 para a senha."""
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = duckdb.connect('financas.db')

    # Sequência para IDs
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_transacoes START 1")

    # 1. Tabela de Transações atualizada
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY DEFAULT nextval('seq_transacoes'),
            valor FLOAT, tipo TEXT, grupo TEXT, subgrupo TEXT, subcategoria TEXT,
            conta TEXT, data DATE, pago BOOLEAN, 
            recorrente BOOLEAN, descricao TEXT
        )
    """)

    # 2. Tabela de Categorias
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cad_categorias (
            grupo TEXT, subgrupo TEXT, subcategoria TEXT, 
            PRIMARY KEY (grupo, subgrupo, subcategoria)
        )
    """)

    # 3. Tabela de Contas
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cad_contas (
            nome TEXT PRIMARY KEY, tipo TEXT, vencimento TEXT
        )
    """)

    # 4. Tabela de Usuários (ATUALIZADO COM APROVAÇÃO)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            senha TEXT,
            email TEXT,
            nivel TEXT,
            aprovado BOOLEAN
        )
    """)

    # --- MIGRAÇÃO AUTOMÁTICA ---
    cols = conn.execute("PRAGMA table_info('transacoes')").fetchall()
    nomes_colunas = [c[1] for c in cols]
    if 'subcategoria' not in nomes_colunas:
        conn.execute("ALTER TABLE transacoes ADD COLUMN subcategoria TEXT DEFAULT 'Geral'")

    cols_cat = conn.execute("PRAGMA table_info('cad_categorias')").fetchall()
    if 'subcategoria' not in [c[1] for c in cols_cat]:
        conn.execute("DROP TABLE IF EXISTS cad_categorias")
        conn.execute("""
            CREATE TABLE cad_categorias (
                grupo TEXT, subgrupo TEXT, subcategoria TEXT, 
                PRIMARY KEY (grupo, subgrupo, subcategoria)
            )
        """)

    # Migração para adicionar a coluna 'aprovado' em tabelas de usuários existentes
    cols_users = conn.execute("PRAGMA table_info('usuarios')").fetchall()
    nomes_colunas_users = [c[1] for c in cols_users]
    if 'aprovado' not in nomes_colunas_users and nomes_colunas_users:
        # Define os usuários antigos como aprovados para não quebrar o acesso atual
        conn.execute("ALTER TABLE usuarios ADD COLUMN aprovado BOOLEAN DEFAULT TRUE")

    # Criação do usuário administrador padrão, se a tabela estiver vazia
    count_users = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    if count_users == 0:
        senha_admin = hash_password("admin123")
        # Admin já nasce com aprovado = TRUE
        conn.execute("INSERT INTO usuarios VALUES ('admin', ?, 'admin@sistema.com', 'Administrador', TRUE)",
                     (senha_admin,))

    conn.close()


def executar_query(sql, dados=None):
    conn = duckdb.connect('financas.db')
    if dados:
        conn.execute(sql, dados)
    else:
        conn.execute(sql)
    conn.close()


def ler_dados(tabela):
    conn = duckdb.connect('financas.db')
    df = conn.execute(f"SELECT * FROM {tabela}").df()
    conn.close()
    return df


def carregar_dados():
    df = ler_dados("transacoes")
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
    return df