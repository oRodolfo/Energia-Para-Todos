import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date

class Database:
    """
    Classe de conexão e operações com PostgreSQL.
    """
    
    def __init__(self):
        """Estabelece conexão com PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                host="localhost",
                database="energia_db",
                user="postgres",
                password="senha123",  # ⚠️ ALTERAR para sua senha
                port="5432"
            )
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print("✅ Conexão com o banco de dados estabelecida com sucesso!")
        except psycopg2.Error as e:
            print("❌ Erro ao conectar ao banco de dados:", e)
            self.conn = None
    
    # ============================================
    # MÉTODOS AUXILIARES
    # ============================================
    
    @staticmethod
    def converter_datas(obj):
        """
        Converte objetos date/datetime para string ISO.
        Necessário para serialização JSON.
        """
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return obj
    
    @staticmethod
    def processar_resultado(resultado):
        """
        Processa resultado de query convertendo datas automaticamente.
        Evita erros de serialização JSON.
        """
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

    def executar(self, query, params=None):
        """
        Executa query SQL e retorna cursor.
        Faz commit automático e rollback em caso de erro.
        """
        try:
            self.cursor.execute(query, params or ())
            self.conn.commit()
            return self.cursor
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise

    def buscar_um(self, query, params=None):
        """
        Busca um único registro.
        Retorna dict ou None.
        """
        try:
            self.cursor.execute(query, params or ())
            resultado = self.cursor.fetchone()
            return self.processar_resultado(resultado)
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise

    def buscar_todos(self, query, params=None):
        """
        Busca múltiplos registros.
        Retorna lista de dicts.
        """
        try:
            self.cursor.execute(query, params or ())
            resultado = self.cursor.fetchall()
            return self.processar_resultado(resultado)
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise

    def fechar(self):
        """Fecha conexão com o banco"""
        self.cursor.close()
        self.conn.close()

    # ============================================
    # AUTENTICAÇÃO E CADASTRO
    # ============================================
    
    def criar_usuario_simples(self, nome, email, senha, tipo_usuario='DOADOR'):
        """
        Cria novo usuário no sistema com:
        - Nome completo (já vem concatenado: firstName + lastName)
        - Email (usado como login)
        - Senha (criptografada com bcrypt)
        - Tipo padrão: DOADOR
        
        Processo:
        1. Cria credencial com senha criptografada
        2. Busca ID do tipo de usuário
        3. Insere usuário na tabela
        4. Retorna id_usuario
        """
        try:
            # 1. Credencial com criptografia bcrypt
            query_credencial = """
            INSERT INTO credencial_usuario (login, senha_hash, senha_salt)
            VALUES (%s, crypt(%s, gen_salt('bf')), gen_salt('bf'))
            RETURNING id_credencial
            """
            cursor = self.executar(query_credencial, (email, senha))
            id_credencial = cursor.fetchone()['id_credencial']

            # 2. Buscar ID do tipo de usuário (DOADOR, BENEFICIARIO, ADMINISTRADOR)
            query_tipo = "SELECT id_tipo FROM tipo_usuario WHERE descricao_tipo = %s"
            tipo = self.buscar_um(query_tipo, (tipo_usuario,))
            id_tipo = tipo['id_tipo'] if tipo else 1

            # 3. Buscar ID do status ATIVO
            query_status = "SELECT id_status FROM status WHERE descricao_status = 'ATIVO'"
            status = self.buscar_um(query_status)
            id_status = status['id_status'] if status else 1

            # ✅ 4. Criar telefone dummy
            query_tel = "INSERT INTO telefone (numero) VALUES (%s) RETURNING id_telefone"
            cursor_tel = self.executar(query_tel, ('00000000000',))
            id_telefone = cursor_tel.fetchone()['id_telefone']

            # 5. Criar usuário
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
        """
        Valida credenciais do usuário:
        - Compara senha usando crypt() do PostgreSQL
        - Verifica se status está ATIVO
        - Retorna dados do usuário se válido
        
        Retorna:
        - dict com id_usuario, nome, email, tipo_usuario, status
        - None se credenciais inválidas
        """
        query = """
            SELECT 
                u.id_usuario, 
                u.nome, 
                u.email,
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
        """
        Atualiza timestamp do último acesso do usuário.
        Usado para auditoria e controle de sessão.
        """
        query = """
            UPDATE credencial_usuario
            SET data_ultimo_login = NOW()
            WHERE login = %s
        """
        self.executar(query, (email,))

    # ============================================
    # DOADOR
    # ============================================

    def criar_doador(self, id_usuario, classificacao='PESSOA_FISICA'):
        """ 
        Cria registro de doador vinculado ao usuário.
        
        Parâmetros:
        - id_usuario: ID do usuário criado anteriormente
        - classificacao: PESSOA_FISICA (padrão) ou PESSOA_JURIDICA
        
        Retorna:
        - id_doador: ID do registro criado
        """
        # Buscar ID da classificação
        query_class = """
            SELECT id_classificacao FROM classificacao_doador 
            WHERE descricao_classificacao = %s
        """
        result = self.buscar_um(query_class, (classificacao,))
        id_classificacao = result['id_classificacao'] if result else 1
        
        # Criar doador
        query = """
            INSERT INTO doador (data_cadastro, id_usuario, id_classificacao)
            VALUES (CURRENT_DATE, %s, %s)
            RETURNING id_doador
        """
        cursor = self.executar(query, (id_usuario, id_classificacao))
        return cursor.fetchone()['id_doador']

    # ============================================
    # CRUD DE USUÁRIOS
    # ============================================

    def listar_usuarios(self, limite=100):
        """
        Lista todos os usuários cadastrados com:
        - Dados básicos (id, nome, email)
        - Informações de doador (se for doador)
        - Dados de credencial (login, último acesso)
        
        Retorna:
        - Lista de dicts com dados dos usuários
        """
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
            LIMIT %s
        """
        return self.buscar_todos(query, (limite,))

    def atualizar_usuario_dados(self, id_usuario, nome, email):
        """
        Atualiza nome e email do usuário.
        
        Retorna:
        - dict com dados atualizados (id_usuario, nome, email)
        """
        try:
            # 1. Buscar id_credencial do usuário
            query_cred = """
                SELECT id_credencial FROM usuario WHERE id_usuario = %s
            """
            result = self.buscar_um(query_cred, (id_usuario,))
        
            if not result:
                raise Exception("Usuário não encontrado")
        
            id_credencial = result['id_credencial']
        
            # 2. Atualizar email na tabela usuario
            query_usuario = """
                UPDATE usuario
                SET nome = %s, email = %s
                WHERE id_usuario = %s
                RETURNING id_usuario, nome, email
            """
            cursor = self.executar(query_usuario, (nome, email, id_usuario))
            usuario_atualizado = cursor.fetchone()
        
            # 3. ✅ Atualizar login na tabela credencial_usuario
            query_login = """
                UPDATE credencial_usuario
                SET login = %s
                WHERE id_credencial = %s
            """
            self.executar(query_login, (email, id_credencial))
        
            return usuario_atualizado
        
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Erro ao atualizar usuário: {str(e)}")

    def atualizar_senha(self, login, senha_atual, senha_nova):
        """
        Altera senha do usuário:
        1. Valida senha atual usando crypt()
        2. Atualiza para nova senha criptografada
        
        Retorna:
        - True: senha alterada com sucesso
        - False: senha atual incorreta
        """
        try:
            cursor = self.executar("""
                UPDATE credencial_usuario
                SET senha_hash = crypt(%s, gen_salt('bf'))
                WHERE login = %s
                AND senha_hash = crypt(%s, senha_hash)
                RETURNING id_credencial
            """, (senha_nova, login, senha_atual))
            
            return cursor.fetchone() is not None
            
        except Exception as e:
            self.conn.rollback()
            raise

    def excluir_usuario_por_email(self, email):
        """
        Exclui usuário e TODAS suas dependências em cascata.
        
        Ordem de exclusão (importante para integridade referencial):
        3. doador (se for doador)
        4. log_auditoria
        5. usuario
        6. credencial_usuario
        
        Retorna:
        - True: usuário excluído com sucesso
        - False: usuário não encontrado
        """
        try:
            # Buscar dados do usuário
            row = self.buscar_um("""
                SELECT 
                    u.id_usuario, 
                    u.id_credencial, 
                    u.id_telefone, 
                    d.id_doador
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
            
            # Se for doador, deletar dependências
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
            
            # Deletar logs de auditoria
            self.executar("DELETE FROM log_auditoria WHERE id_usuario = %s", (id_usuario,))
            
            # Deletar usuário
            self.executar("DELETE FROM usuario WHERE id_usuario = %s", (id_usuario,))
            
            # Deletar credencial
            if id_cred:
                self.executar("DELETE FROM credencial_usuario WHERE id_credencial = %s", (id_cred,))
            
            # Deletar telefone
            if id_telefone:
                self.executar("DELETE FROM telefone WHERE id_telefone = %s", (id_telefone,))
            
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erro ao excluir usuário: {e}")
            raise

    # ============================================
    # LOG DE AUDITORIA
    # ============================================

    def registrar_log_auditoria(self, id_usuario, tipo_acao, ip_acesso=None, detalhes=None):
        """
        ✅ USADO EM: routes.login() e routes.cadastro_doador()
        
        Registra ação do usuário para auditoria:
        - LOGIN, LOGOUT, CADASTRO, DOACAO, etc.
        
        Parâmetros:
        - id_usuario: ID do usuário que executou a ação
        - tipo_acao: Tipo da ação (LOGIN, CADASTRO, etc.)
        - ip_acesso: IP de origem (opcional)
        - detalhes: Descrição adicional (opcional)
        
        Retorna:
        - id_log: ID do registro criado
        """
        # Buscar ID do tipo de ação
        query_tipo = "SELECT id_tipo_acao FROM tipo_acao WHERE descricao_tipo_acao = %s"
        tipo = self.buscar_um(query_tipo, (tipo_acao,))
        id_tipo_acao = tipo['id_tipo_acao'] if tipo else 1

        # Buscar ID do tipo de dispositivo (WEB)
        query_disp = """
            SELECT id_tipo_dispositivo FROM tipo_dispositivo 
            WHERE descricao_tipo_dispositivo = 'WEB'
        """
        disp = self.buscar_um(query_disp)
        id_disp = disp['id_tipo_dispositivo'] if disp else 1

        # Buscar ID do status (SUCESSO)
        query_status = """
            SELECT id_status_log FROM status_log 
            WHERE descricao_status_log = 'SUCESSO'
        """
        status = self.buscar_um(query_status)
        id_status = status['id_status_log'] if status else 1

        # Inserir log
        query = """
            INSERT INTO log_auditoria 
            (ip_acesso, data_hora, detalhes, id_usuario, id_tipo_acao, id_tipo_dispositivo, id_status_log)
            VALUES (%s, NOW(), %s, %s, %s, %s, %s)
            RETURNING id_log
        """
        cursor = self.executar(
            query, 
            (ip_acesso, detalhes, id_usuario, id_tipo_acao, id_disp, id_status)
        )
        return cursor.fetchone()['id_log']