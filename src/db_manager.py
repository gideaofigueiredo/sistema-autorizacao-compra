import sqlite3
import os
import atexit
import csv
from datetime import datetime
from utils_path import get_base_path, get_data_path

class DBManager:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(get_data_path(), "banco_autcompras.sqlite")
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
            caminho_forn = os.path.join(get_data_path(), "AutComprasMaster - Fornecedores.csv")
            if os.path.exists(caminho_forn):
                try:
                    with open(caminho_forn, newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            try:
                                nome = row.get("nome_razao_social", "").strip()
                                cpf_cnpj = row.get("cpf_cnpj", "").strip()
                                if nome:
                                    self.cursor.execute('''
                                        INSERT INTO fornecedores (nome_razao_social, cpf_cnpj, sincronizado) 
                                        VALUES (?, ?, 1)
                                    ''', (nome, cpf_cnpj))
                            except Exception:
                                continue
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

    def sincronizar_de_nuvem(self, auth_rows, forn_rows):
        """Sincroniza do Sheets para o SQLite. auth_rows e forn_rows devem ser listas de listas."""
        # 1. Fornecedores
        existing_forn = set(f["cpf_cnpj"] for f in self.obter_todos_fornecedores() if f.get("cpf_cnpj"))
        for row in forn_rows:
            if len(row) >= 2:
                nome = row[0].strip()
                cpf_cnpj = row[1].strip()
                if cpf_cnpj and cpf_cnpj not in existing_forn:
                    self.cursor.execute('''
                        INSERT INTO fornecedores (nome_razao_social, cpf_cnpj, sincronizado) 
                        VALUES (?, ?, 1)
                    ''', (nome, cpf_cnpj))
                    existing_forn.add(cpf_cnpj)

        # 2. Autorizações
        self.cursor.execute("SELECT numero_gerado FROM autorizacoes")
        existing_auth = set(r[0] for r in self.cursor.fetchall() if r[0])
        
        max_num_mes_atual = 0
        mes_ano_atual = datetime.now().strftime("%m%y")

        for row in auth_rows:
            if not row or len(row) < 9: continue
            num = row[0].strip()
            if not num: continue

            if "-" in num:
                partes = num.split("-", 1)
                mes_ano = partes[0]
                cont = partes[1]
                if mes_ano == mes_ano_atual and cont.isdigit():
                    max_num_mes_atual = max(max_num_mes_atual, int(cont))

            if num not in existing_auth:
                try:
                    valor_pecas = float(row[6].replace(".", "").replace(",", ".")) if row[6] else 0.0
                    valor_mo = float(row[7].replace(".", "").replace(",", ".")) if row[7] else 0.0
                    total = valor_pecas + valor_mo
                    self.cursor.execute('''
                        INSERT INTO autorizacoes (
                            numero_gerado, data, fornecedor, orcamento, placa, km,
                            valor_pecas, valor_mao_de_obra, total_autorizado, observacao, sincronizado
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    ''', (
                        num, row[1], row[2], row[3], row[4], row[5],
                        valor_pecas, valor_mo, total, row[8]
                    ))
                    existing_auth.add(num)
                except Exception as e:
                    print(f"[sincronizar_de_nuvem] erro na linha {num}: {e}")

        # 3. Atualizar sequência
        self.cursor.execute("SELECT mes_ano, ultimo_numero FROM controle_sequencia WHERE id = 1")
        resultado = self.cursor.fetchone()
        mes_ano_banco = resultado[0] if resultado else None
        ultimo_contador = resultado[1] if resultado else 0

        if mes_ano_banco == mes_ano_atual:
            novo_contador = max(ultimo_contador, max_num_mes_atual)
            self.cursor.execute("UPDATE controle_sequencia SET ultimo_numero = ? WHERE id = 1", (novo_contador,))
        else:
            if max_num_mes_atual > 0:
                self.cursor.execute("UPDATE controle_sequencia SET ultimo_numero = ?, mes_ano = ? WHERE id = 1", (max_num_mes_atual, mes_ano_atual))
                
        self.conn.commit()

# Singleton do DBManager
db = DBManager()
