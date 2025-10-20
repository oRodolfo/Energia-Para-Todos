import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date
import json

class Database:
    """Conexão direta com PostgreSQL - Estrutura Simplificada"""
    
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host="localhost",
                database="energia_db",
                user="postgres",
                password="senha123",
                port="5432"
            )
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print("✅ Conexão com o banco de dados estabelecida com sucesso!")
        except psycopg2.Error as e:
            print("❌ Erro ao conectar ao banco de dados:", e)
            self.conn = None
    
    # ============================================
    # CONVERSÃO DE DADOS
    # ============================================
    
    @staticmethod
    def converter_datas(obj):
        """Converte objetos date/datetime para string"""
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return obj
    
    @staticmethod
    def processar_resultado(resultado):
        """Processa resultado convertendo datas"""
        if resultado is None:
            return None
        if isinstance(resultado, list):
            return [
                {k: Database.converter_datas(v) for k, v in row.items()}
                for row in resultado
            ]
        if isinstance(resultado, dict):
            return {k: Database.converter_datas(v) for k, v in resultado.items()}
        return resultado

    # ============================================
    # EXECUÇÃO DE QUERIES - CORRIGIDO
    # ============================================
    
    def executar(self, query, params=None):
        """Executa query e retorna cursor"""
        try:
            self.cursor.execute(query, params or ())
            self.conn.commit()
            return self.cursor
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise

    def buscar_um(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            resultado = self.cursor.fetchone()
            return self.processar_resultado(resultado)
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise

    def buscar_todos(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            resultado = self.cursor.fetchall()
            return self.processar_resultado(resultado)
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise

    def fechar(self):
        self.cursor.close()
        self.conn.close()

    # ============================================
    # USUÁRIO - CADASTRO SIMPLIFICADO - CORRIGIDO
    # ============================================
    
    def criar_usuario_simples(self, nome, email, senha, tipo_usuario='DOADOR'):
        """Cria usuário com apenas: nome, email e senha"""
        try:
            # 1. Telefone padrão
            query_telefone = "INSERT INTO telefone (numero) VALUES (%s) RETURNING id_telefone"
            cursor = self.executar(query_telefone, ('00000000000',))
            id_telefone = cursor.fetchone()['id_telefone']

            # 2. Credencial
            query_credencial = """
                INSERT INTO credencial_usuario (login, senha_hash, senha_salt)
                VALUES (%s, crypt(%s, gen_salt('bf')), gen_salt('bf'))
                RETURNING id_credencial
            """
            cursor = self.executar(query_credencial, (email, senha))
            id_credencial = cursor.fetchone()['id_credencial']

            # 3. Tipo de usuário
            query_tipo = "SELECT id_tipo FROM tipo_usuario WHERE descricao_tipo = %s"
            tipo = self.buscar_um(query_tipo, (tipo_usuario,))
            id_tipo = tipo['id_tipo'] if tipo else 1

            # 4. Status ATIVO
            query_status = "SELECT id_status FROM status WHERE descricao_status = 'ATIVO'"
            status = self.buscar_um(query_status)
            id_status = status['id_status'] if status else 1

            # 5. Usuário
            query_usuario = """
                INSERT INTO usuario (nome, email, id_telefone, id_tipo, id_status, cep, id_credencial)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id_usuario
            """
            cursor = self.executar(
                query_usuario, 
                (nome, email, id_telefone, id_tipo, id_status, '00000-000', id_credencial)
            )
            id_usuario = cursor.fetchone()['id_usuario']
            return id_usuario

        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Erro ao criar usuário: {str(e)}")

    def validar_login(self, email, senha):
        """Valida login"""
        query = """
            SELECT 
                u.id_usuario, u.nome, u.email,
                tu.descricao_tipo as tipo_usuario,
                s.descricao_status as status
            FROM usuario u
            JOIN credencial_usuario c ON u.id_credencial = c.id_credencial
            JOIN tipo_usuario tu ON u.id_tipo = tu.id_tipo
            JOIN status s ON u.id_status = s.id_status
            WHERE c.login = %s
            AND c.senha_hash = crypt(%s, c.senha_hash)
            AND s.descricao_status = 'ATIVO'
        """
        return self.buscar_um(query, (email, senha))

    def atualizar_ultimo_login(self, email):
        """Atualiza data_ultimo_login"""
        query = """
            UPDATE credencial_usuario
            SET data_ultimo_login = NOW()
            WHERE login = %s
        """
        self.executar(query, (email,))

    # ============================================
    # DOADOR - CORRIGIDO
    # ============================================

    def criar_doador(self, id_usuario, classificacao='PESSOA_FISICA'):
        """Cria registro de doador"""
        query_class = """
            SELECT id_classificacao FROM classificacao_doador 
            WHERE descricao_classificacao = %s
        """
        result = self.buscar_um(query_class, (classificacao,))
        id_classificacao = result['id_classificacao'] if result else 1
        
        query = """
            INSERT INTO doador (data_cadastro, id_usuario, id_classificacao)
            VALUES (CURRENT_DATE, %s, %s)
            RETURNING id_doador
        """
        cursor = self.executar(query, (id_usuario, id_classificacao))
        return cursor.fetchone()['id_doador']

    def buscar_doador_por_usuario(self, id_usuario):
        """Busca doador completo"""
        query = """
            SELECT 
                d.id_doador, d.id_usuario, d.data_cadastro,
                cd.descricao_classificacao as classificacao,
                u.nome, u.email,
                COALESCE(t.numero, '00000000000') as telefone,
                COALESCE(u.cep, '00000-000') as cep,
                COALESCE(SUM(c.quantidade_disponivel_kwh), 0) as total_kwh_doados,
                COUNT(DISTINCT c.id_credito) as total_doacoes
            FROM doador d
            JOIN usuario u ON d.id_usuario = u.id_usuario
            LEFT JOIN telefone t ON u.id_telefone = t.id_telefone
            JOIN classificacao_doador cd ON d.id_classificacao = cd.id_classificacao
            LEFT JOIN credito c ON d.id_doador = c.id_doador
            WHERE d.id_usuario = %s
            GROUP BY d.id_doador, d.id_usuario, d.data_cadastro, 
                     cd.descricao_classificacao, u.nome, u.email, t.numero, u.cep
        """
        return self.buscar_um(query, (id_usuario,))

    # ============================================
    # BENEFICIÁRIO
    # ============================================

    def criar_beneficiario(self, id_usuario, renda_familiar=1000.0, consumo_medio_kwh=150.0, num_moradores=1):
        """Cria beneficiário com valores padrão"""
        try:
            query_renda = """
                INSERT INTO renda_beneficiario (valor_renda, periodo)
                VALUES (%s, 'MENSAL')
                RETURNING id_renda
            """
            cursor = self.executar(query_renda, (renda_familiar,))
            id_renda = cursor.fetchone()['id_renda']

            query_consumo = """
                INSERT INTO consumo_beneficiario (media_kwh, periodo)
                VALUES (%s, 'MENSAL')
                RETURNING id_consumo
            """
            cursor = self.executar(query_consumo, (consumo_medio_kwh,))
            id_consumo = cursor.fetchone()['id_consumo']

            query_status = """
                SELECT id_status_beneficiario FROM status_beneficiario 
                WHERE descricao_status_beneficiario = 'AGUARDANDO_APROVACAO'
            """
            status = self.buscar_um(query_status)
            id_status = status['id_status_beneficiario'] if status else 1

            query_beneficiario = """
                INSERT INTO beneficiario 
                (num_moradores, id_usuario, id_renda, id_consumo, id_status_beneficiario)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_beneficiario
            """
            cursor = self.executar(
                query_beneficiario,
                (num_moradores, id_usuario, id_renda, id_consumo, id_status)
            )
            return cursor.fetchone()['id_beneficiario']

        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Erro ao criar beneficiário: {str(e)}")

    # ============================================
    # CRÉDITO
    # ============================================

    def listar_creditos_doador(self, id_doador):
        """Lista créditos de um doador para o dashboard"""
        query = """
            SELECT 
                c.id_credito, 
                c.quantidade_disponivel_kwh, 
                c.data_expiracao,
                sc.descricao_status AS status,
                COALESCE(hc.data_movimento, CURRENT_DATE) AS data_criacao
            FROM credito c
            JOIN status_credito sc ON c.id_status_credito = sc.id_status_credito
            LEFT JOIN historico_credito hc ON c.id_credito = hc.id_credito
            WHERE c.id_doador = %s
            ORDER BY c.data_expiracao DESC
        """
        return self.buscar_todos(query, (id_doador,))

    def listar_creditos_disponiveis(self):
        """Lista créditos disponíveis para distribuição"""
        query = """
            SELECT 
            c.id_credito, c.id_doador, c.quantidade_disponivel_kwh, c.data_expiracao
            FROM credito c
            JOIN status_credito sc ON c.id_status_credito = sc.id_status_credito
            WHERE sc.descricao_status IN ('DISPONIVEL', 'PARCIALMENTE_UTILIZADO')
                AND c.quantidade_disponivel_kwh > 0
                AND c.data_expiracao > CURRENT_DATE
            """
        return self.buscar_todos(query)

    def criar_credito(self, id_doador, quantidade_kwh, data_expiracao):
        """Cria um crédito para o doador"""
        query_status = """
            SELECT id_status_credito 
            FROM status_credito 
            WHERE descricao_status = 'DISPONIVEL'
        """
        status = self.buscar_um(query_status)
        id_status = status['id_status_credito'] if status else 1

        query = """
            INSERT INTO credito 
                (quantidade_disponivel_kwh, data_expiracao, id_doador, id_status_credito)
            VALUES (%s, %s, %s, %s)
            RETURNING id_credito
        """
        cur = self.executar(query, (quantidade_kwh, data_expiracao, id_doador, id_status))
        return cur.fetchone()['id_credito']

    def registrar_historico_credito(self, id_credito, quantidade_kwh):
        """Registra um movimento no histórico do crédito"""
        query = """
            INSERT INTO historico_credito (quantidade_kwh, data_movimento, id_credito)
            VALUES (%s, CURRENT_DATE, %s)
        """
        self.executar(query, (quantidade_kwh, id_credito))

    def atualizar_credito(self, id_credito, quantidade_disponivel, novo_status):
        """Atualiza a quantidade e o status de um crédito"""
        query_status = "SELECT id_status_credito FROM status_credito WHERE descricao_status = %s"
        status = self.buscar_um(query_status, (novo_status,))
        id_status = status['id_status_credito'] if status else 1

        query = """
            UPDATE credito 
            SET quantidade_disponivel_kwh = %s, id_status_credito = %s
            WHERE id_credito = %s
        """
        self.executar(query, (quantidade_disponivel, id_status, id_credito))

    # ============================================
    # TRANSAÇÃO / HISTÓRICO
    # ============================================

    def criar_transacao(self, id_beneficiario, id_credito, quantidade_kwh, tipo_movimento='DISTRIBUICAO'):
        """Cria transação"""
        query_tipo = """
            SELECT id_tipo_movimentacao FROM tipo_movimento 
            WHERE descricao_tipo = %s
        """
        tipo = self.buscar_um(query_tipo, (tipo_movimento,))
        id_tipo_movimento = tipo['id_tipo_movimentacao'] if tipo else 1

        query_status = """
            SELECT id_status_transacao FROM status_transacao 
            WHERE descricao_status = 'CONCLUIDA'
        """
        status = self.buscar_um(query_status)
        id_status = status['id_status_transacao'] if status else 1

        query = """
            INSERT INTO transacao 
            (quantidade_kwh, data_transacao, id_beneficiario, id_status_transacao, id_tipo_movimentacao)
            VALUES (%s, CURRENT_DATE, %s, %s, %s)
            RETURNING id_transacao
        """
        cursor = self.executar(
            query,
            (quantidade_kwh, id_beneficiario, id_status, id_tipo_movimento)
        )
        return cursor.fetchone()['id_transacao']

    # ============================================
    # LOG DE AUDITORIA
    # ============================================

    def registrar_log_auditoria(self, id_usuario, tipo_acao, ip_acesso=None, detalhes=None):
        """Registra log"""
        query_tipo = "SELECT id_tipo_acao FROM tipo_acao WHERE descricao_tipo_acao = %s"
        tipo = self.buscar_um(query_tipo, (tipo_acao,))
        id_tipo_acao = tipo['id_tipo_acao'] if tipo else 1

        query_disp = """
            SELECT id_tipo_dispositivo FROM tipo_dispositivo 
            WHERE descricao_tipo_dispositivo = 'WEB'
        """
        disp = self.buscar_um(query_disp)
        id_disp = disp['id_tipo_dispositivo'] if disp else 1

        query_status = """
            SELECT id_status_log FROM status_log 
            WHERE descricao_status_log = 'SUCESSO'
        """
        status = self.buscar_um(query_status)
        id_status = status['id_status_log'] if status else 1

        query = """
            INSERT INTO log_auditoria 
            (ip_acesso, data_hora, detalhes, id_usuario, id_tipo_acao, id_tipo_dispositivo, id_status_log)
            VALUES (%s, NOW(), %s, %s, %s, %s, %s)
            RETURNING id_log
        """
        cursor = self.executar(
            query, (ip_acesso, detalhes, id_usuario, id_tipo_acao, id_disp, id_status)
        )
        return cursor.fetchone()['id_log']

    # ============================================
    # CRUD USUÁRIO
    # ============================================

    def atualizar_usuario_dados(self, id_usuario, nome, email):
        query = """
            UPDATE usuario
                SET nome = %s,
                    email = %s
            WHERE id_usuario = %s
        RETURNING id_usuario, nome, email
        """
        cur = self.executar(query, (nome, email, id_usuario))
        return cur.fetchone()

    def atualizar_senha(self, login, senha_atual, senha_nova):
        try:
            cur = self.executar("""
                UPDATE credencial_usuario
                    SET senha_hash = crypt(%s, gen_salt('bf'))
                WHERE login = %s
                    AND senha_hash = crypt(%s, senha_hash)
                RETURNING id_credencial
            """, (senha_nova, login, senha_atual))
            return cur.fetchone() is not None
        except Exception as e:
            self.conn.rollback()
            raise

    def excluir_usuario_por_email(self, email):
        """Exclui usuário e todas suas dependências"""
        try:
            # 1. Buscar dados do usuário
            row = self.buscar_um("""
                SELECT u.id_usuario, u.id_credencial, u.id_telefone, d.id_doador
                FROM usuario u
                LEFT JOIN doador d ON d.id_usuario = u.id_usuario
                WHERE u.email = %s
            """, (email,))
            
            if not row:
                return False
            
            id_usuario = row['id_usuario']
            id_cred = row['id_credencial']
            id_telefone = row['id_telefone']
            id_doador = row['id_doador']
            
            # 2. Deletar em ordem (das dependências para as tabelas principais)
            
            # Se for doador, deletar créditos e históricos primeiro
            if id_doador:
                # Deletar histórico de créditos
                self.executar("""
                    DELETE FROM historico_credito 
                    WHERE id_credito IN (
                        SELECT id_credito FROM credito WHERE id_doador = %s
                    )
                """, (id_doador,))
                
                # Deletar créditos
                self.executar("DELETE FROM credito WHERE id_doador = %s", (id_doador,))
                
                # Deletar doador
                self.executar("DELETE FROM doador WHERE id_doador = %s", (id_doador,))
            
            # 3. Deletar logs de auditoria
            self.executar("DELETE FROM log_auditoria WHERE id_usuario = %s", (id_usuario,))
            
            # 4. Deletar usuário
            self.executar("DELETE FROM usuario WHERE id_usuario = %s", (id_usuario,))
            
            # 5. Deletar credencial
            if id_cred:
                self.executar("DELETE FROM credencial_usuario WHERE id_credencial = %s", (id_cred,))
            
            # 6. Deletar telefone (se não for padrão)
            if id_telefone:
                self.executar("DELETE FROM telefone WHERE id_telefone = %s", (id_telefone,))
            
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erro ao excluir usuário: {e}")
            raise

    def listar_usuarios(self, limite=100):
        query = """
            SELECT 
                u.id_usuario,
                u.nome,
                u.email,
                d.id_doador,
                d.data_cadastro AS data_cadastro_doador,
                cu.login,
                cu.data_ultimo_login
            FROM usuario u
            LEFT JOIN doador d ON d.id_usuario = u.id_usuario
            LEFT JOIN credencial_usuario cu ON cu.id_credencial = u.id_credencial
            ORDER BY u.id_usuario DESC
            LIMIT 100
        """
        return self.buscar_todos(query)

    def listar_beneficiarios_aprovados(self):
        """Lista beneficiários aprovados"""
        query = """
            SELECT 
                b.id_beneficiario, b.id_usuario, b.num_moradores,
                u.nome, u.email,
                COALESCE(t.numero, '00000000000') as telefone,
                COALESCE(u.cep, '00000-000') as cep,
                r.valor_renda as renda_familiar,
                c.media_kwh as consumo_medio_kwh,
                0 as saldo_creditos_kwh
            FROM beneficiario b
            JOIN usuario u ON b.id_usuario = u.id_usuario
            LEFT JOIN telefone t ON u.id_telefone = t.id_telefone
            JOIN renda_beneficiario r ON b.id_renda = r.id_renda
            JOIN consumo_beneficiario c ON b.id_consumo = c.id_consumo
            JOIN status_beneficiario sb ON b.id_status_beneficiario = sb.id_status_beneficiario
            WHERE sb.descricao_status_beneficiario = 'APROVADO'
        """
        return self.buscar_todos(query)