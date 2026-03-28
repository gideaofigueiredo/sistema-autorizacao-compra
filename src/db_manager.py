import sqlite3
import os
import atexit
from datetime import datetime

class DBManager:
    def __init__(self, db_path="storage/banco_autcompras.sqlite"):
        # Garantir que a pasta storage existe
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._criar_tabelas()
        
        # Fecha a conexão limpoamento ao terminar
        atexit.register(self.fechar_conexao)

    def _criar_tabelas(self):
        # Tabela principal de autorizações
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS autorizacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_gerado TEXT,
                data TEXT,
                fornecedor TEXT,
                orcamento TEXT,
                placa TEXT,
                km TEXT,
                valor_pecas REAL,
                valor_mao_de_obra REAL,
                total_autorizado REAL,
                observacao TEXT,
                sincronizado INTEGER DEFAULT 0
            )
        ''')
        
        # Tabela para manter o controle da sequência numeração local
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS controle_sequencia (
                id INTEGER PRIMARY KEY,
                ultimo_numero INTEGER
            )
        ''')
        
        # Add mes_ano column if it doesn't exist
        try:
            self.cursor.execute("ALTER TABLE controle_sequencia ADD COLUMN mes_ano TEXT")
        except sqlite3.OperationalError:
            pass
            
        # Tabela para fornecedores offline
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS fornecedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_razao_social TEXT,
                cpf_cnpj TEXT,
                sincronizado INTEGER DEFAULT 0
            )
        ''')
        
        # Inicializa o controle de sequencia se estiver em branco
        self.cursor.execute("SELECT COUNT(*) FROM controle_sequencia")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("INSERT INTO controle_sequencia (id, ultimo_numero, mes_ano) VALUES (1, 0, ?)", (datetime.now().strftime("%m%y"),))
            
        self.conn.commit()
        self._importar_csv_fornecedores()

    def _importar_csv_fornecedores(self):
        self.cursor.execute("SELECT COUNT(*) FROM fornecedores")
        if self.cursor.fetchone()[0] == 0:
            caminho_forn = "storage/AutComprasMaster - Fornecedores.csv"
            if os.path.exists(caminho_forn):
                import pandas as pd
                try:
                    df_forn = pd.read_csv(caminho_forn, encoding="utf-8", sep=",")
                    df_forn = df_forn.fillna("")
                    for row in df_forn.itertuples(index=False):
                        try:
                            nome = str(row.nome_razao_social)
                            cpf_cnpj = str(row.cpf_cnpj)
                        except AttributeError:
                            continue
                        self.cursor.execute('''
                            INSERT INTO fornecedores (nome_razao_social, cpf_cnpj, sincronizado) 
                            VALUES (?, ?, 1)
                        ''', (nome, cpf_cnpj))
                    self.conn.commit()
                except Exception:
                    pass

    def obter_e_incrementar_numero_local(self):
        """
        Retorna a próxima string formatada 'MMYY-XYZ' e atualiza o contador do BD
        baseado no mês/ano atual. Se o mês virou, reinicia o contador para 1,
        se não incrementa normalmente.
        """
        mes_ano_atual = datetime.now().strftime("%m%y")
        
        self.cursor.execute("SELECT mes_ano, ultimo_numero FROM controle_sequencia WHERE id = 1")
        resultado = self.cursor.fetchone()
        
        mes_ano_banco = resultado[0] if resultado else None
        ultimo_contador = resultado[1] if resultado else 0
        
        if mes_ano_banco == mes_ano_atual:
            proximo_contador = ultimo_contador + 1
        else:
            # Virou o mês, resetamos contador para 1
            proximo_contador = 1
        
        # Atualiza a tabela controle_sequencia para registro geral
        self.cursor.execute("UPDATE controle_sequencia SET ultimo_numero = ?, mes_ano = ? WHERE id = 1", (proximo_contador, mes_ano_atual))
        self.conn.commit()
        
        numero_formatado = f"{mes_ano_atual}-{str(proximo_contador).zfill(3)}"
        return numero_formatado

    def salvar_autorizacao_local(self, dados: dict):
        """Salva a autorização no SQLite e a marca como não sincronizada (0)"""
        self.cursor.execute('''
            INSERT INTO autorizacoes (
                numero_gerado, data, fornecedor, orcamento, placa, km,
                valor_pecas, valor_mao_de_obra, total_autorizado, observacao, sincronizado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (
            dados.get("numero"),
            dados.get("data"),
            dados.get("fornecedor"),
            dados.get("orcamento"),
            dados.get("placa"),
            dados.get("km"),
            dados.get("valor_pecas"),
            dados.get("valor_mao_de_obra"),
            dados.get("total_autorizado"),
            dados.get("observacao")
        ))
        self.conn.commit()

    def obter_pendentes_sincronizacao(self):
        """Busca todas as autorizações que ainda não foram enviadas pro Google Sheets"""
        self.cursor.execute('''
            SELECT * FROM autorizacoes WHERE sincronizado = 0 ORDER BY id ASC
        ''')
        # Retorna lista de dicionários por conveniência
        colunas = [desc[0] for desc in self.cursor.description]
        return [dict(zip(colunas, linha)) for linha in self.cursor.fetchall()]

    def marcar_como_sincronizado(self, obj_id):
        """Seta o status de sincronizado como true/1 no banco."""
        self.cursor.execute("UPDATE autorizacoes SET sincronizado = 1 WHERE id = ?", (obj_id,))
        self.conn.commit()

    # --- FORNECEDORES ---
    def salvar_fornecedor_local(self, nome_razao_social: str, cpf_cnpj: str):
        self.cursor.execute('''
            INSERT INTO fornecedores (nome_razao_social, cpf_cnpj, sincronizado)
            VALUES (?, ?, 0)
        ''', (nome_razao_social, cpf_cnpj))
        self.conn.commit()

    def obter_todos_fornecedores(self):
        self.cursor.execute("SELECT * FROM fornecedores ORDER BY nome_razao_social ASC")
        colunas = [desc[0] for desc in self.cursor.description]
        return [dict(zip(colunas, linha)) for linha in self.cursor.fetchall()]

    def obter_fornecedores_pendentes(self):
        self.cursor.execute("SELECT * FROM fornecedores WHERE sincronizado = 0 ORDER BY id ASC")
        colunas = [desc[0] for desc in self.cursor.description]
        return [dict(zip(colunas, linha)) for linha in self.cursor.fetchall()]

    def marcar_fornecedor_sincronizado(self, obj_id):
        self.cursor.execute("UPDATE fornecedores SET sincronizado = 1 WHERE id = ?", (obj_id,))
        self.conn.commit()

    def fechar_conexao(self):
        if self.conn:
            self.conn.close()

# Singleton do DBManager
db = DBManager()
