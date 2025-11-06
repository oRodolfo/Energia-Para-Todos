import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Set, Tuple
from psycopg2 import extensions

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
                password="senha123", 
                port="5432"
            )
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print("✅ Conexão com o banco de dados estabelecida com sucesso!")
        except psycopg2.Error as e:
            print("❌ Erro ao conectar ao banco de dados:", e)
            self.conn = None
    def _rollback_if_needed(self):
        """
        Se houver transação aberta, faz rollback para voltar ao estado IDLE.
        Evita 'set_session cannot be used inside a transaction'.
        """
        if not self.conn:
            return
        st = self.conn.get_transaction_status()
        # Usa as constantes CORRETAS do psycopg2
        if st in (extensions.TRANSACTION_STATUS_INTRANS, extensions.TRANSACTION_STATUS_ACTIVE):
            try:
                self.conn.rollback()
            except Exception:
                pass

    def _set_autocommit_safe(self, on: bool):
        """
        Muda o autocommit com segurança: antes, sai de qualquer transação ativa.
        """
        self._rollback_if_needed()
        self.conn.autocommit = on
    
    # ============================================
    # MÉTODOS AUXILIARES
    # ============================================
    
    @staticmethod
    def converter_datas(obj):
        """
        Converte objetos date/datetime/Decimal para tipos serializáveis.
        """
        from decimal import Decimal
    
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return obj
    
    @staticmethod
    def processar_resultado(resultado):
        """
        Processa resultado de query convertendo tipos automaticamente.
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
        - Faz commit automático SOMENTE quando autocommit está True.
        - Em transações manuais (autocommit=False), quem chama decide commit/rollback.
        """
        try:
            self.cursor.execute(query, params or ())
            if self.conn.autocommit:  # <<< só commita se estiver em autocommit
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

            # 4. Criar telefone dummy
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
            # Garantir que a criação do usuário seja confirmada no banco
            try:
                self.conn.commit()
            except Exception:
                # Se commit falhar, tenta rollback para deixar estado consistente
                try:
                    self.conn.rollback()
                except Exception:
                    pass

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
    

    def criar_beneficiario_simples(self, id_usuario):
        """
        Cria registro de beneficiário vinculado ao usuário.
        ✅ NOVO: Método para garantir criação do beneficiário
    
        Parâmetros:
        - id_usuario: ID do usuário criado anteriormente
    
        Retorna:
        - id_beneficiario: ID do registro criado
        """
        try:
            # Busca ID do status AGUARDANDO_APROVACAO
            query_status = """
                SELECT id_status_beneficiario FROM status_beneficiario 
                WHERE descricao_status_beneficiario = 'AGUARDANDO_APROVACAO'
            """
            status = self.buscar_um(query_status)
            id_status = status['id_status_beneficiario'] if status else 1
        
            # Cria beneficiário
            query = """
                INSERT INTO beneficiario (
                    id_usuario, 
                    num_moradores, 
                    id_status_beneficiario
                )
                VALUES (%s, 1, %s)
                RETURNING id_beneficiario
            """
            cursor = self.executar(query, (id_usuario, id_status))
            id_beneficiario = cursor.fetchone()['id_beneficiario']
            # Confirma a inserção para que outras operações (em especial
            # aquelas que fazem rollback antes de iniciar transação) vejam o registro
            try:
                self.conn.commit()
            except Exception:
                try:
                    self.conn.rollback()
                except Exception:
                    pass

            print(f"✅ Beneficiário criado: id_beneficiario={id_beneficiario} para usuario_id={id_usuario}")

            return id_beneficiario
        
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Erro ao criar beneficiário: {str(e)}")

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
        # Retorna dados mais completos para UI administrativa:
        # - hash da senha (senha_hash)
        # - id_doador (se houver)
        # - id_beneficiario (se houver)
        # - última ação registrada na tabela de logs (tipo de ação e timestamp)
        query = """
            SELECT 
                u.id_usuario,
                u.nome,
                u.email,
                d.id_doador,
                b.id_beneficiario,
                d.data_cadastro AS data_cadastro_doador,
                cu.login,
                cu.data_ultimo_login,
                cu.senha_hash,
                ultima.ultima_acao,
                ultima.data_hora AS ultima_acao_data
            FROM usuario u
            LEFT JOIN doador d ON d.id_usuario = u.id_usuario
            LEFT JOIN beneficiario b ON b.id_usuario = u.id_usuario
            LEFT JOIN credencial_usuario cu ON cu.id_credencial = u.id_credencial
            LEFT JOIN LATERAL (
                SELECT ta.descricao_tipo_acao AS ultima_acao, la.data_hora
                FROM log_auditoria la
                LEFT JOIN tipo_acao ta ON la.id_tipo_acao = ta.id_tipo_acao
                WHERE la.id_usuario = u.id_usuario
                ORDER BY la.data_hora DESC
                LIMIT 1
            ) ultima ON TRUE
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
        1. doador (se for doador)
        2. log_auditoria
        3. usuario
        4. credencial_usuario
        
        Retorna:
        - True: usuário excluído com sucesso
        - False: usuário não encontrado
        """
        try:
            row = self.buscar_um("""
                SELECT 
                    u.id_usuario, 
                    u.id_credencial, 
                    u.id_telefone, 
                    d.id_doador,
                    b.id_beneficiario
                FROM usuario u
                LEFT JOIN doador d ON d.id_usuario = u.id_usuario
                LEFT JOIN beneficiario b ON b.id_usuario = u.id_usuario
                WHERE u.email = %s
            """, (email,))
            if not row:
                return False

            id_usuario = row['id_usuario']
            id_cred    = row['id_credencial']
            id_tel     = row['id_telefone']
            id_doador  = row['id_doador']
            id_benef   = row['id_beneficiario']

            # GARANTA autocommit LIGADO
            self._set_autocommit_safe(True)

            # Se for BENEFICIÁRIO, apague dependências primeiro
            if id_benef:
                self.executar("DELETE FROM fila_espera WHERE id_beneficiario = %s", (id_benef,))
                self.executar("DELETE FROM transacao   WHERE id_beneficiario = %s", (id_benef,))
                self.executar("DELETE FROM beneficiario WHERE id_beneficiario = %s", (id_benef,))

            # Se for DOADOR, apague créditos/histórico e depois o doador
            if id_doador:
                self.executar("""
                    DELETE FROM historico_credito 
                    WHERE id_credito IN (SELECT id_credito FROM credito WHERE id_doador = %s)
                """, (id_doador,))
                self.executar("DELETE FROM transacao WHERE id_credito IN (SELECT id_credito FROM credito WHERE id_doador = %s)", (id_doador,))
                self.executar("DELETE FROM credito   WHERE id_doador = %s", (id_doador,))
                self.executar("DELETE FROM doador    WHERE id_doador = %s", (id_doador,))

            # Logs vinculados ao usuário
            self.executar("DELETE FROM log_auditoria WHERE id_usuario = %s", (id_usuario,))

            # Por fim, o usuário e suas credenciais/telefone
            self.executar("DELETE FROM usuario WHERE id_usuario = %s", (id_usuario,))
            if id_cred:
                self.executar("DELETE FROM credencial_usuario WHERE id_credencial = %s", (id_cred,))
            if id_tel:
                self.executar("DELETE FROM telefone WHERE id_telefone = %s", (id_tel,))
            
            return True

        except Exception as e:
            print(f"❌ Erro ao excluir usuário: {e}")
            raise

    # ============================================
    # LOG DE AUDITORIA
    # ============================================

    def registrar_log_auditoria(self, id_usuario, tipo_acao, ip_acesso=None, detalhes=None):
        """
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
        try:
            # ✅ Buscar ID do tipo de ação
            query_tipo = "SELECT id_tipo_acao FROM tipo_acao WHERE descricao_tipo_acao = %s"
            tipo = self.buscar_um(query_tipo, (tipo_acao,))
            id_tipo_acao = tipo['id_tipo_acao'] if tipo else 1

            # ✅ Buscar ID do tipo de dispositivo (WEB)
            query_disp = """
                SELECT id_tipo_dispositivo FROM tipo_dispositivo 
                WHERE descricao_tipo_dispositivo = 'WEB'
            """
            disp = self.buscar_um(query_disp)
            id_disp = disp['id_tipo_dispositivo'] if disp else 1

            # ✅ Buscar ID do status (SUCESSO)
            query_status = """
                SELECT id_status_log FROM status_log 
                WHERE descricao_status_log = 'SUCESSO'
            """
            status = self.buscar_um(query_status)
            id_status = status['id_status_log'] if status else 1

            # ✅ Inserir log (permite NULL em id_usuario)
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
            resultado = cursor.fetchone()
            return resultado['id_log'] if resultado else None
        
        except Exception as e:
            print(f"❌ ERRO ao registrar log: {e}")
            # Não lança exceção para não quebrar o fluxo principal
            return None

    # ============================================
    # GESTÃO DE CRÉDITOS
    # ============================================
    
    def criar_credito(
        self, 
        id_doador: int, 
        quantidade_kwh: float, 
        data_expiracao: Optional[date] = None
    ) -> int:
        """
        Cria novo crédito de energia para um doador.
        
        Args:
            id_doador: ID do doador
            quantidade_kwh: Quantidade em kWh
            data_expiracao: Data de expiração (opcional, padrão 12 meses)
        
        Returns:
            ID do crédito criado
        """
        try:
            # Define expiração padrão se não fornecida
            if data_expiracao is None:
                from datetime import timedelta
                data_expiracao = date.today() + timedelta(days=365)
            
            # Busca ID do status DISPONIVEL
            query_status = """
                SELECT id_status_credito FROM status_credito 
                WHERE descricao_status = 'DISPONIVEL'
            """
            status = self.buscar_um(query_status)
            id_status = status['id_status_credito'] if status else 1
            
            # Insere crédito
            query = """
                INSERT INTO credito (
                    quantidade_disponivel_kwh,
                    data_expiracao,
                    id_doador,
                    id_status_credito
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id_credito
            """
            cursor = self.executar(query, (quantidade_kwh, data_expiracao, id_doador, id_status))
            id_credito = cursor.fetchone()['id_credito']
            
            # Registra no histórico
            self.registrar_historico_credito(
                id_credito=id_credito,
                evento='CRIACAO',
                detalhe={'quantidade_kwh': quantidade_kwh, 'data_expiracao': str(data_expiracao)}
            )
            # Garante que a inserção foi persistida para leituras em outras requisições
            try:
                self.conn.commit()
            except Exception:
                try:
                    self.conn.rollback()
                except Exception:
                    pass

            return id_credito
            
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Erro ao criar crédito: {str(e)}")
    
    def listar_creditos(
        self, 
        id_doador: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list:
        """
        Lista créditos com paginação.
        
        Args:
            id_doador: Filtrar por doador (None = todos, requer ADMIN)
            limit: Registros por página
            offset: Deslocamento
        
        Returns:
            Lista de dicts com dados dos créditos
        """
        query = """
            SELECT 
                c.id_credito,
                c.quantidade_disponivel_kwh,
                c.data_expiracao,
                c.id_doador,
                sc.descricao_status AS status,
                d.data_cadastro,
                u.nome AS nome_doador,
                u.email AS email_doador
            FROM credito c
            JOIN status_credito sc ON c.id_status_credito = sc.id_status_credito
            JOIN doador d ON c.id_doador = d.id_doador
            JOIN usuario u ON d.id_usuario = u.id_usuario
        """
        
        params = []
        if id_doador:
            query += " WHERE c.id_doador = %s"
            params.append(id_doador)
        
        query += " ORDER BY c.id_credito DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        return self.buscar_todos(query, tuple(params))
    
    def registrar_historico_credito(
        self,
        id_credito: int,
        evento: str,
        detalhe: Optional[dict] = None
    ) -> None:
        """
        Registra evento no histórico do crédito.
        
        Args:
            id_credito: ID do crédito
            evento: Tipo de evento (CRIACAO, CONSUMO, EXPIRACAO, etc)
            detalhe: Dados adicionais em JSON
        """
        import json
        
        # Busca quantidade atual para registrar
        query_qtd = "SELECT quantidade_disponivel_kwh FROM credito WHERE id_credito = %s"
        result = self.buscar_um(query_qtd, (id_credito,))
        quantidade_atual = result['quantidade_disponivel_kwh'] if result else 0
        
        query = """
            INSERT INTO historico_credito (
                quantidade_kwh,
                data_movimento,
                id_credito
            )
            VALUES (%s, CURRENT_DATE, %s)
        """
        self.executar(query, (quantidade_atual, id_credito))
    
    def atualizar_status_credito(self, id_credito: int) -> None:
        """
        Atualiza status do crédito baseado na quantidade disponível e expiração.
        
        Args:
            id_credito: ID do crédito
        """
        query = "SELECT atualizar_status_credito(%s)"
        self.executar(query, (id_credito,))
    
    # ============================================
    # FILA DE ESPERA
    # ============================================
    
    def entrar_na_fila(
        self,
        id_beneficiario: int,
        renda_familiar: float,
        consumo_medio_kwh: float,
        num_moradores: int
    ) -> int:
        """
        ✅ CORRIGIDO: Usa _set_autocommit_safe para evitar conflitos
        """
        try:
            print(f"🔵 entrar_na_fila chamado para id_beneficiario={id_beneficiario}")
        
            # ✅ USA O MÉTODO SEGURO para desligar autocommit
            self._set_autocommit_safe(False)
        
            # Verifica se já está na fila AGUARDANDO
            query_existe = """
                SELECT f.id_fila 
                FROM fila_espera f
                JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila
                WHERE f.id_beneficiario = %s 
                    AND sf.descricao_status_fila = 'AGUARDANDO'
            """
            existe = self.buscar_um(query_existe, (id_beneficiario,))
        
            if existe:
                self.conn.rollback()
                self._set_autocommit_safe(True)
                print(f"⚠️ Beneficiário já está na fila: id_fila={existe['id_fila']}")
                raise ValueError("Beneficiário já está na fila de espera")
        
            # Busca ID do status AGUARDANDO
            query_status = """
                SELECT id_status_fila FROM status_fila 
                WHERE descricao_status_fila = 'AGUARDANDO'
            """
            status = self.buscar_um(query_status)
            id_status = status['id_status_fila'] if status else 1
        
            print(f"📊 Status AGUARDANDO: id={id_status}")
        
            # Calcula prioridade 
            query_prioridade = """
                SELECT calcular_prioridade(%s, %s, %s, 0) AS prioridade
            """
            result_prior = self.buscar_um(
                query_prioridade,
                (renda_familiar, consumo_medio_kwh, num_moradores)
            )
            prioridade = result_prior['prioridade']
        
            print(f"🎯 Prioridade calculada: {prioridade}")
        
            # ✅ CRÍTICO: Verifica se beneficiário existe com LOCK
            query_verifica = "SELECT id_beneficiario FROM beneficiario WHERE id_beneficiario = %s FOR UPDATE"
            verifica = self.buscar_um(query_verifica, (id_beneficiario,))
        
            if not verifica:
                self.conn.rollback()
                self._set_autocommit_safe(True)
                print(f"❌ ERRO CRÍTICO: Beneficiário {id_beneficiario} não existe!")
                raise ValueError(f"Beneficiário {id_beneficiario} não encontrado")
        
            print(f"✅ Beneficiário {id_beneficiario} confirmado no banco")
        
            # Insere na fila
            query = """
                INSERT INTO fila_espera (
                    id_beneficiario,
                    prioridade,
                    data_entrada,
                    id_status_fila,
                    renda_familiar,
                    consumo_medio_kwh,
                    num_moradores,
                    tempo_espera_dias
                )
                VALUES (%s, %s, NOW(), %s, %s, %s, %s, 0)
                RETURNING id_fila
            """
            self.cursor.execute(
                query,
                (id_beneficiario, prioridade, id_status, renda_familiar, consumo_medio_kwh, num_moradores)
            )
        
            resultado = self.cursor.fetchone()
            if not resultado:
                self.conn.rollback()
                self._set_autocommit_safe(True)
                raise Exception("Falha ao inserir na fila")
        
            id_fila = resultado['id_fila']
        
            # ✅ COMMIT EXPLÍCITO
            self.conn.commit()
        
            print(f"✅ Inserido na fila com sucesso: id_fila={id_fila}")
        
            # Verifica APÓS commit
            self._set_autocommit_safe(True)
            verifica_pos = self.buscar_um("SELECT id_beneficiario FROM beneficiario WHERE id_beneficiario = %s", (id_beneficiario,))
            if not verifica_pos:
                print(f"❌ ALERTA: Beneficiário {id_beneficiario} desapareceu após commit!")
            else:
                print(f"✅ Beneficiário {id_beneficiario} ainda existe após inserção")
        
            return id_fila
        
        except ValueError as ve:
            self.conn.rollback()
            self._set_autocommit_safe(True)
            print(f"⚠️ ValueError: {ve}")
            raise
        except Exception as e:
            print(f"❌ ERRO em entrar_na_fila: {e}")
            import traceback
            traceback.print_exc()
            self.conn.rollback()
            self._set_autocommit_safe(True)
            raise Exception(f"Erro ao entrar na fila: {str(e)}")
    
    def listar_fila(self, top: int = 50) -> list:
        """
        Lista beneficiários na fila ordenados por prioridade.
        
        Args:
            top: Número máximo de registros
        
        Returns:
            Lista ordenada por prioridade desc, data_entrada asc
        """
        query = """
            SELECT * FROM v_fila_priorizada
            LIMIT %s
        """
        return self.buscar_todos(query, (top,))
    
    # ============================================
    # DISTRIBUIÇÃO AUTOMÁTICA
    # ============================================
    
    def executar_distribuicao(self, limite: int = 10) -> dict:
        """
        Distribui créditos para os beneficiários prioritários.
        - Marca ATENDIDO apenas se o beneficiário recebeu > 0 kWh
        - Conta beneficiários atendidos como DISTINCT por id_beneficiario
        - Garante reset de autocommit em qualquer saída
        """
        self._set_autocommit_safe(False)
        try:
            # 1) Créditos disponíveis com lock
            query_creditos = """
                SELECT c.id_credito, c.id_doador, c.quantidade_disponivel_kwh, c.data_expiracao
                FROM credito c
                JOIN status_credito sc ON c.id_status_credito = sc.id_status_credito
                WHERE sc.descricao_status IN ('DISPONIVEL', 'PARCIALMENTE_UTILIZADO')
                    AND c.quantidade_disponivel_kwh > 0
                    AND (c.data_expiracao IS NULL OR c.data_expiracao > CURRENT_DATE)
                ORDER BY c.data_expiracao NULLS LAST, c.id_credito
                FOR UPDATE SKIP LOCKED
            """
            creditos = self.buscar_todos(query_creditos)

            if not creditos:
                self.conn.rollback()
                return {
                    'total_distribuido': 0.0,
                    'beneficiarios_atendidos': 0,
                    'creditos_consumidos': 0,
                    'transacoes': [],
                    'mensagem': 'Nenhum crédito disponível'
                }

            total_kwh_disponivel = float(sum(c['quantidade_disponivel_kwh'] for c in creditos))

            # 2) Top beneficiários com lock
            query_beneficiarios = """
                SELECT f.id_fila, f.id_beneficiario, f.prioridade, f.consumo_medio_kwh,
                    u.nome, u.email
                FROM fila_espera f
                JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila
                JOIN beneficiario b ON f.id_beneficiario = b.id_beneficiario
                JOIN usuario u ON b.id_usuario = u.id_usuario
                WHERE sf.descricao_status_fila = 'AGUARDANDO'
                ORDER BY f.prioridade DESC, f.data_entrada ASC
                LIMIT %s
                FOR UPDATE OF f SKIP LOCKED
            """
            beneficiarios = self.buscar_todos(query_beneficiarios, (limite,))

            if not beneficiarios:
                self.conn.rollback()
                return {
                    'total_distribuido': 0.0,
                    'beneficiarios_atendidos': 0,
                    'creditos_consumidos': 0,
                    'transacoes': [],
                    'mensagem': 'Nenhum beneficiário na fila'
                }

            # Pré-buscas de IDs estáticos
            id_status_trans = self.buscar_um(
                "SELECT id_status_transacao FROM status_transacao WHERE descricao_status = 'CONCLUIDA'")['id_status_transacao']
            id_tipo_mov = self.buscar_um(
                "SELECT id_tipo_movimentacao FROM tipo_movimento WHERE descricao_tipo = 'DISTRIBUICAO'")['id_tipo_movimentacao']
            id_status_fila_atendido = self.buscar_um(
                "SELECT id_status_fila FROM status_fila WHERE descricao_status_fila = 'ATENDIDO'")['id_status_fila']

            # 3) Alocações alvo (proporcional)
            # Observação: não devemos distribuir MAIS do que o beneficiário solicitou.
            # Antes havia um "kwh_minimo = max(consumo_medio, 50)" e em seguida
            # "kwh_alvo = max(kwh_alocado, kwh_minimo)" — isso fazia com que, quando
            # existia apenas um beneficiário, ele recebesse todo o montante disponível
            # mesmo que tivesse solicitado menos (causando o problema relatado).
            # Correção: limitar o alvo ao valor solicitado quando houver uma solicitação.
            soma_prioridades = float(sum(b['prioridade'] for b in beneficiarios)) or 1.0
            alocacoes = []
            for benef in beneficiarios:
                peso = float(benef['prioridade']) / soma_prioridades
                kwh_alocado = total_kwh_disponivel * peso
                solicitado = float(benef.get('consumo_medio_kwh') or 0)

                # Se o beneficiário informou um valor solicitado (>0), não distribuímos
                # mais do que esse valor. Caso contrário, usamos a alocação proporcional.
                if solicitado > 0:
                    kwh_alvo = min(kwh_alocado, solicitado)
                else:
                    kwh_alvo = kwh_alocado

                alocacoes.append({
                    'id_beneficiario': benef['id_beneficiario'],
                    'id_fila': benef['id_fila'],
                    'kwh_alvo': float(kwh_alvo),
                    'nome': benef['nome']
                })

            # 4) Distribuição efetiva
            total_distribuido = 0.0
            transacoes_criadas = []
            creditos_usados = set()

            # percorre beneficiários
            for alocacao in alocacoes:
                kwh_restante = float(alocacao['kwh_alvo'])
                distribuido_benef = 0.0  # <<< acumulador POR beneficiário

                # consome de vários créditos enquanto houver alvo e saldo
                for credito in creditos:
                    if kwh_restante <= 0.0:
                        break
                    if float(credito['quantidade_disponivel_kwh']) <= 0.0:
                        continue

                    kwh_consumir = float(min(kwh_restante, float(credito['quantidade_disponivel_kwh'])))

                    # cria transação
                    cursor_trans = self.executar(
                        """
                        INSERT INTO transacao (
                            quantidade_kwh, data_transacao, id_beneficiario,
                            id_status_transacao, id_tipo_movimentacao, id_credito
                        )
                        VALUES (%s, CURRENT_DATE, %s, %s, %s, %s)
                        RETURNING id_transacao
                        """,
                        (kwh_consumir, alocacao['id_beneficiario'], id_status_trans, id_tipo_mov, credito['id_credito'])
                    )
                    id_transacao = cursor_trans.fetchone()['id_transacao']

                    # debita crédito
                    nova_qtd = float(credito['quantidade_disponivel_kwh']) - kwh_consumir
                    self.executar(
                        "UPDATE credito SET quantidade_disponivel_kwh = %s WHERE id_credito = %s",
                        (nova_qtd, credito['id_credito'])
                    )

                    # status do crédito
                    self.atualizar_status_credito(credito['id_credito'])

                    # histórico (snapshot)
                    self.registrar_historico_credito(
                        id_credito=credito['id_credito'],
                        evento='CONSUMO',
                        detalhe={
                            'quantidade_consumida': kwh_consumir,
                            'id_beneficiario': alocacao['id_beneficiario'],
                            'id_transacao': id_transacao
                        }
                    )

                    # atualiza acumuladores
                    credito['quantidade_disponivel_kwh'] = nova_qtd
                    total_distribuido += kwh_consumir
                    distribuido_benef += kwh_consumir         # <<< soma do beneficiário
                    kwh_restante -= kwh_consumir
                    creditos_usados.add(credito['id_credito'])

                    transacoes_criadas.append({
                        'id_transacao': id_transacao,
                        'id_beneficiario': alocacao['id_beneficiario'],
                        'nome_beneficiario': alocacao['nome'],
                        'id_credito': credito['id_credito'],
                        'quantidade_kwh': kwh_consumir
                    })

                # MARCA ATENDIDO **APENAS** SE ESTE BENEFICIÁRIO RECEBEU ALGO
                if distribuido_benef > 0.0:
                    self.executar(
                        "UPDATE fila_espera SET id_status_fila = %s WHERE id_fila = %s",
                        (id_status_fila_atendido, alocacao['id_fila'])
                    )
                # else: mantém AGUARDANDO (ou poderia ajustar prioridade/tempo)

            # 5) Auditoria da execução
            self.registrar_log_auditoria(
                id_usuario=None,
                tipo_acao='DISTRIBUICAO',
                detalhes=f"Distribuídos {total_distribuido:.2f} kWh em {len(transacoes_criadas)} transações"
            )

            # 6) Commit e retorno
            self.conn.commit()

            beneficiarios_distintos = { t['id_beneficiario'] for t in transacoes_criadas }
            return {
                'total_distribuido': round(total_distribuido, 2),
                'beneficiarios_atendidos': len(beneficiarios_distintos),
                'creditos_consumidos': len(creditos_usados),
                'transacoes': transacoes_criadas
            }

        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Erro na distribuição: {str(e)}")
        finally:
            self._set_autocommit_safe(True)


