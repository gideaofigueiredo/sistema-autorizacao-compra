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
        
        # Inicializa o controle de sequencia se estiver em branco
        self.cursor.execute("SELECT COUNT(*) FROM controle_sequencia")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("INSERT INTO controle_sequencia (id, ultimo_numero) VALUES (1, 0)")
            
        self.conn.commit()

    def obter_e_incrementar_numero_local(self):
        """
        Retorna a próxima string formatada 'MMYY-XYZ' e atualiza o contador do BD
        baseado no mês/ano atual. Se o mês virou, reinicia o contador para 1,
        se não incrementa normalmente.
        """
        mes_ano_atual = datetime.now().strftime("%m%y")
        
        # Precisamos saber se já estamos no mesmo prefixo
        # Podemos olhar a última autorização gerada hoje ou olhar a tabela controle_sequencia.
        # Mas para simplificar, se o mês vira, recomeçamos de 1.
        self.cursor.execute("SELECT numero_gerado FROM autorizacoes ORDER BY id DESC LIMIT 1")
        resultado = self.cursor.fetchone()
        
        ultimo_contador = 0
        if resultado:
            ultimo_numero_str = resultado[0] # Ex: "0326-001"
            if ultimo_numero_str.startswith(mes_ano_atual):
                try:
                    ultimo_contador = int(ultimo_numero_str.split('-')[1])
                except ValueError:
                    ultimo_contador = 0
            else:
                # Mudou o mês/ano, reinicia o contador
                ultimo_contador = 0
        
        proximo_contador = ultimo_contador + 1
        
        # Atualiza a tabela controle_sequencia para registro geral
        self.cursor.execute("UPDATE controle_sequencia SET ultimo_numero = ? WHERE id = 1", (proximo_contador,))
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

    def fechar_conexao(self):
        if self.conn:
            self.conn.close()

# Singleton do DBManager
db = DBManager()
