#Caminho para o diretorio BackEnd 
import os, sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "BackEnd")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from datetime import datetime, timedelta
from database import Database
import json

class Routes:
    """
    Classe responsável por gerenciar as rotas da aplicação.
    
    implementações importantes:
    - id_beneficiario sempre carregado na sessão após login
    - Verificação de sessão antes de cada operação
    - Logs detalhados para debug
    - Escolha e troca de perfil
    - Completar cadastro
    - Funcionalidades do Doador
    """
    
    _sessao_global = {}

    def __init__(self):
        self.db = Database()
        self.sessao = Routes._sessao_global
    
    # AUTENTICAÇÃO
    def login(self, dados):
        email = dados.get('email')
        senha = dados.get('password')
        
        usuario = self.db.validar_login(email, senha)
        
        if usuario:
            # Salva dados básicos na sessão
            Routes._sessao_global['usuario_id'] = usuario['id_usuario']
            Routes._sessao_global['nome'] = usuario['nome']
            Routes._sessao_global['email'] = usuario['email']
            Routes._sessao_global['tipo'] = usuario['tipo_usuario']
            Routes._sessao_global['id_doador'] = None
            Routes._sessao_global['id_beneficiario'] = None
            
            if usuario['tipo_usuario'] == 'BENEFICIARIO':
                print(f"Login detectado como BENEFICIÁRIO. usuario_id={usuario['id_usuario']}")
                query_benef = "SELECT id_beneficiario FROM beneficiario WHERE id_usuario = %s"
                result = self.db.buscar_um(query_benef, (usuario['id_usuario'],))
                
                if result:
                    Routes._sessao_global['id_beneficiario'] = result['id_beneficiario']
                    print(f"Login beneficiário: id_beneficiario={result['id_beneficiario']}")
                else:
                    # Cria beneficiário se não existir
                    print(f"Beneficiário não encontrado, criando...")
                    id_benef = self.db.criar_beneficiario_simples(usuario['id_usuario'])
                    Routes._sessao_global['id_beneficiario'] = id_benef
                    print(f"Beneficiário criado: id_beneficiario={id_benef}")
            
            elif usuario['tipo_usuario'] == 'DOADOR':
                query_doador = "SELECT id_doador FROM doador WHERE id_usuario = %s"
                result = self.db.buscar_um(query_doador, (usuario['id_usuario'],))
                
                if result:
                    Routes._sessao_global['id_doador'] = result['id_doador']
                    print(f"Login doador: id_doador={result['id_doador']}")
            
            self.db.atualizar_ultimo_login(email)
            
            self.db.registrar_log_auditoria(
                id_usuario=usuario['id_usuario'],
                tipo_acao='LOGIN',
                detalhes=f"Login realizado por {email}"
            )

            # Verifica se usuário já tem tipo definido
            if not usuario['tipo_usuario'] or usuario['tipo_usuario'] == 'NOVO':
                return {
                    'sucesso': True,
                    'mensagem': 'Login realizado! Escolha seu perfil.',
                    'redirect': '/selecionar-perfil'
                }

            # Se tem tipo, verifica se perfil está completo
            perfil_completo = self.verificar_perfil_completo(usuario['id_usuario'], usuario['tipo_usuario'])
            if not perfil_completo:
                return {
                    'sucesso': True,
                    'mensagem': 'Login realizado! Complete seu cadastro.',
                    'redirect': '/completar-cadastro'
                }
            
            # Se tudo estiver ok (com perfil com todas as informações completas), redireciona para o painel apropriado
            redirect = '/painel-beneficiario' if usuario['tipo_usuario'] == 'BENEFICIARIO' else '/painel-doador'
            print(f"Sessão global após login: {Routes._sessao_global}")
            self.sessao = Routes._sessao_global.copy()

            return {
                'sucesso': True,
                'mensagem': 'Login realizado com sucesso!',
                'redirect': redirect
            }
        else:
            return {
                'sucesso': False,
                'mensagem': 'Email ou senha incorretos'
            }
    
    #Retorna sessão completa após cadastro
    def cadastro_inicial(self, dados):
        try:
            nome_completo = f"{dados.get('firstName', '')} {dados.get('lastName', '')}".strip()
    
            id_usuario = self.db.criar_usuario_simples(
                nome=nome_completo.strip(),
                email=dados['email'],
                senha=dados['password'],
                tipo_usuario='NOVO'
            )
    
            Routes._sessao_global['usuario_id'] = id_usuario
            Routes._sessao_global['nome'] = nome_completo
            Routes._sessao_global['email'] = dados['email']
            Routes._sessao_global['tipo'] = 'NOVO'
            Routes._sessao_global['id_beneficiario'] = None
            Routes._sessao_global['id_doador'] = None
        
            self.sessao = Routes._sessao_global.copy()
        
            print(f"Cadastro inicial completo: usuario_id={id_usuario}")
            print(f"Sessão criada: {Routes._sessao_global}")
        
            self.db.registrar_log_auditoria(
                id_usuario=id_usuario,
                tipo_acao='CADASTRO',
                detalhes=f"Novo usuário cadastrado: {nome_completo}"
            )
    
            return {
                'sucesso': True,
                'mensagem': 'Cadastro realizado! Escolha seu perfil.',
                'redirect': '/selecionar-perfil'
            }
    
        except Exception as e:
            erro_str = str(e).lower()
            print(f"ERRO CADASTRO: {e}")
            import traceback
            traceback.print_exc()
        
            if 'unique' in erro_str or 'credencial_usuario_login_key' in erro_str or 'duplicat' in erro_str or 'chave' in erro_str:
                return {
                    'sucesso': False,
                    'mensagem': 'Esse e-mail já está sendo utilizado. Tente fazer o login ou faça o cadastro com outro e-mail.'
                }
        
            return {
                'sucesso': False,
                'mensagem': 'Erro ao cadastrar. Verifique seus dados e tente novamente.'
            }
        
    # COMPLETAR CADASTRO DO BENEFICIÁRIO
    def completar_cadastro_beneficiario(self, dados):
        try:
            usuario_id = self.sessao.get('usuario_id')
            id_beneficiario = self.sessao.get('id_beneficiario')
            
            print(f"completar_cadastro_beneficiario: usuario_id={usuario_id}, id_beneficiario={id_beneficiario}")
            
            if not usuario_id:
                return {'sucesso': False, 'mensagem': 'Usuário não autenticado'}

            #verifica se beneficiário existe
            if not id_beneficiario:
                query_existe = "SELECT id_beneficiario FROM beneficiario WHERE id_usuario = %s"
                result = self.db.buscar_um(query_existe, (usuario_id,))
                
                if result:
                    id_beneficiario = result['id_beneficiario']
                    Routes._sessao_global['id_beneficiario'] = id_beneficiario
                    print(f"Beneficiário encontrado: id_beneficiario={id_beneficiario}")
                else:
                    id_beneficiario = self.db.criar_beneficiario_simples(usuario_id)
                    Routes._sessao_global['id_beneficiario'] = id_beneficiario
                    print(f"Beneficiário criado: id_beneficiario={id_beneficiario}")

            # Busca dados atuais
            row = self.db.buscar_um(
                "SELECT id_renda, id_consumo FROM beneficiario WHERE id_beneficiario = %s", 
                (id_beneficiario,)
            )
            
            id_renda = row.get('id_renda') if row else None
            id_consumo = row.get('id_consumo') if row else None
        
            renda_familiar = float(dados.get('renda_familiar', 0))
            consumo_medio = float(dados.get('consumo_medio_kwh', 0))
            num_moradores = int(dados.get('num_moradores', 1))
        
            # Cria ou atualiza RENDA
            if id_renda:
                self.db.executar("""
                    UPDATE renda_beneficiario 
                    SET valor_renda = %s 
                    WHERE id_renda = %s
                """, (renda_familiar, id_renda))
            else:
                cursor_renda = self.db.executar("""
                    INSERT INTO renda_beneficiario (valor_renda, periodo)
                    VALUES (%s, 'MENSAL')
                    RETURNING id_renda
                """, (renda_familiar,))
                id_renda = cursor_renda.fetchone()['id_renda']
        
            # Cria ou atualiza CONSUMO
            if id_consumo:
                self.db.executar("""
                    UPDATE consumo_beneficiario 
                    SET media_kwh = %s 
                    WHERE id_consumo = %s
                """, (consumo_medio, id_consumo))
            else:
                cursor_consumo = self.db.executar("""
                    INSERT INTO consumo_beneficiario (media_kwh, periodo)
                    VALUES (%s, 'MENSAL')
                    RETURNING id_consumo
                """, (consumo_medio,))
                id_consumo = cursor_consumo.fetchone()['id_consumo']
        
            # Atualiza beneficiário
            self.db.executar("""
                UPDATE beneficiario
                SET id_renda = %s, id_consumo = %s, num_moradores = %s
                WHERE id_beneficiario = %s
            """, (id_renda, id_consumo, num_moradores, id_beneficiario))
            
            print(f"Cadastro beneficiário atualizado: id_beneficiario={id_beneficiario}")
        
            self.db.registrar_log_auditoria(
                id_usuario=usuario_id,
                tipo_acao='CADASTRO',
                detalhes=f'Cadastro beneficiário completo (renda: {renda_familiar}, consumo: {consumo_medio} kWh)'
            )

            return {
                'sucesso': True, 
                'mensagem': 'Cadastro completo! Você já pode solicitar créditos.',
                'redirect': '/painel-beneficiario'
            }

        except Exception as e:
            print(f"ERRO COMPLETAR BENEFICIARIO: {e}")
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'mensagem': str(e)}
    
    # DASHBOARD DO BENEFICIÁRIO
    def obter_dados_beneficiario(self):
        try:
            id_beneficiario = self.sessao.get('id_beneficiario')
            usuario_id = self.sessao.get('usuario_id')

            print(f"📦 Sessão atual em obter_dados_beneficiario: {self.sessao}")
            print(f"🔍 obter_dados_beneficiario: id_beneficiario={id_beneficiario}, usuario_id={usuario_id}")
        
            if not id_beneficiario and usuario_id:
                query_benef = "SELECT id_beneficiario FROM beneficiario WHERE id_usuario = %s"
                result = self.db.buscar_um(query_benef, (usuario_id,))
            
                if result:
                    id_beneficiario = result['id_beneficiario']
                    Routes._sessao_global['id_beneficiario'] = id_beneficiario
                    print(f"id_beneficiario recuperado da base: {id_beneficiario}")
                else:
                    print(f"Beneficiário não existe no banco para usuario_id={usuario_id}")
                    return {'sucesso': False, 'mensagem': 'Beneficiário não encontrado. Complete seu cadastro.'}
        
            if not id_beneficiario:
                print(f"id_beneficiario não encontrado na sessão")
                return {'sucesso': False, 'mensagem': 'Sessão inválida. Faça login novamente.'}
    
            print(f"🔍 Buscando dados do beneficiário id={id_beneficiario}")
    
            # Dados básicos
            query_dados = """
                SELECT b.id_beneficiario, 
                    COALESCE(b.num_moradores, 0) AS num_moradores,
                    COALESCE(rb.valor_renda, 0) AS valor_renda, 
                    COALESCE(cb.media_kwh, 0) AS media_kwh,
                    COALESCE(sb.descricao_status_beneficiario, 'AGUARDANDO_APROVACAO') AS descricao_status_beneficiario,
                    u.nome, u.email
                FROM beneficiario b
                JOIN usuario u ON b.id_usuario = u.id_usuario
                LEFT JOIN renda_beneficiario rb ON b.id_renda = rb.id_renda
                LEFT JOIN consumo_beneficiario cb ON b.id_consumo = cb.id_consumo
                LEFT JOIN status_beneficiario sb ON b.id_status_beneficiario = sb.id_status_beneficiario
                WHERE b.id_beneficiario = %s
            """
            dados_basicos = self.db.buscar_um(query_dados, (id_beneficiario,))

            if not dados_basicos:
                print(f"ERRO: Nenhum dado retornado para id_beneficiario={id_beneficiario}")
                return {'sucesso': False, 'mensagem': 'Dados do beneficiário não encontrados'}
        
            print(f"Dados básicos encontrados: {dados_basicos}")

            # Posição na fila
            query_fila = """
                SELECT 
                    f.id_fila, 
                    f.prioridade, 
                    f.data_entrada,
                    sf.descricao_status_fila,
                    (
                        SELECT COUNT(*) + 1 
                        FROM fila_espera f2 
                        JOIN status_fila sf2 ON f2.id_status_fila = sf2.id_status_fila
                        WHERE sf2.descricao_status_fila = 'AGUARDANDO'
                          AND (
                            f2.prioridade > f.prioridade 
                            OR (f2.prioridade = f.prioridade AND f2.data_entrada < f.data_entrada)
                        )
                    ) AS posicao_fila
                FROM fila_espera f
                JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila
                WHERE f.id_beneficiario = %s
                    AND sf.descricao_status_fila = 'AGUARDANDO'
                ORDER BY f.data_entrada DESC
                LIMIT 1
            """
            fila_info = self.db.buscar_um(query_fila, (id_beneficiario,))
    
            # Histórico
            query_historico = """
                SELECT 
                    f.id_fila,
                    f.consumo_medio_kwh AS quantidade_kwh,
                    f.data_entrada AS data_transacao,
                    sf.descricao_status_fila AS descricao_status,
                    COALESCE(
                        (
                            SELECT COUNT(*) + 1 
                            FROM fila_espera f2 
                            JOIN status_fila sf2 ON f2.id_status_fila = sf2.id_status_fila
                            WHERE sf2.descricao_status_fila = 'AGUARDANDO'
                                AND (
                                    f2.prioridade > f.prioridade 
                                    OR (f2.prioridade = f.prioridade AND f2.data_entrada < f.data_entrada)
                                )
                        ),
                        0
                    ) AS posicao_fila,
                    CASE 
                        WHEN sf.descricao_status_fila = 'ATENDIDO' THEN 'SIM'
                        WHEN sf.descricao_status_fila = 'AGUARDANDO' THEN 'NÃO'
                        ELSE 'CANCELADO'
                    END AS foi_atendido
                FROM fila_espera f
                JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila
                WHERE f.id_beneficiario = %s
                ORDER BY f.data_entrada DESC
            """
            historico = self.db.buscar_todos(query_historico, (id_beneficiario,))
    
            #Total recebido APENAS de transações CONCLUÍDAS
            query_total = """
                SELECT COALESCE(SUM(t.quantidade_kwh), 0) AS total_recebido
                FROM transacao t
                JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
                WHERE t.id_beneficiario = %s
                    AND st.descricao_status = 'CONCLUIDA'
                    AND t.id_credito IS NOT NULL
            """
            result_total = self.db.buscar_um(query_total, (id_beneficiario,))
            total_recebido = float(result_total['total_recebido']) if result_total else 0
    
            return {
                'sucesso': True,
                'dados': {
                    **dados_basicos,
                    'total_recebido_kwh': round(total_recebido, 2),
                    'fila': fila_info,
                    'historico': historico
                }
            }
    
        except Exception as e:
            print(f"ERRO OBTER DADOS BENEFICIARIO: {e}")
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'mensagem': str(e)}
    
    def criar_solicitacao_beneficiario(self, dados):
        try:
            id_beneficiario = self.sessao.get('id_beneficiario')
            
            print(f"🔵 criar_solicitacao: id_beneficiario={id_beneficiario}")
            
            if not id_beneficiario:
                return {'sucesso': False, 'mensagem': 'Beneficiário não encontrado na sessão'}
            
            quantidade_solicitada = float(dados.get('quantidade_kwh', 0))
            
            if quantidade_solicitada <= 0:
                return {'sucesso': False, 'mensagem': 'Quantidade inválida'}
            
            # Busca dados do beneficiário
            query_benef = """
                SELECT b.num_moradores, rb.valor_renda, cb.media_kwh
                FROM beneficiario b
                LEFT JOIN renda_beneficiario rb ON b.id_renda = rb.id_renda
                LEFT JOIN consumo_beneficiario cb ON b.id_consumo = cb.id_consumo
                WHERE b.id_beneficiario = %s
            """
            benef_dados = self.db.buscar_um(query_benef, (id_beneficiario,))
            
            if not benef_dados:
                return {'sucesso': False, 'mensagem': 'Dados do beneficiário não encontrados'}
            
            consumo_medio = float(benef_dados['media_kwh'] or 0)
            
            # Validação
            if consumo_medio > 0 and quantidade_solicitada > consumo_medio:
                return {
                    'sucesso': False,
                    'mensagem': f'Você só pode solicitar até {consumo_medio} kWh (seu consumo médio mensal)'
                }
            
            #Verifica se já está na fila
            query_fila_existe = """
                SELECT f.id_fila 
                FROM fila_espera f
                JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila
                WHERE f.id_beneficiario = %s 
                  AND sf.descricao_status_fila = 'AGUARDANDO'
            """
            fila_existe = self.db.buscar_um(query_fila_existe, (id_beneficiario,))
            
            if fila_existe:
                return {
                    'sucesso': False,
                    'mensagem': 'Você já possui uma solicitação aguardando.'
                }
            
            #Insere na fila
            self.db.entrar_na_fila(
                id_beneficiario=id_beneficiario,
                renda_familiar=float(benef_dados['valor_renda'] or 0),
                consumo_medio_kwh=quantidade_solicitada,
                num_moradores=int(benef_dados['num_moradores'] or 1)
            )
            
            mensagem = f'Solicitação de {quantidade_solicitada} kWh registrada! Você entrou na fila.'
            
            #Tenta distribuição
            try:
                resultado_dist = self.db.executar_distribuicao(limite=10)
                if resultado_dist.get('beneficiarios_atendidos', 0) > 0:
                    mensagem += f" {resultado_dist['beneficiarios_atendidos']} beneficiário(s) atendido(s)!"
            except Exception as e:
                print(f"Distribuição falhou: {e}")
            
            return {'sucesso': True, 'mensagem': mensagem}
            
        except Exception as e:
            print(f"ERRO CRIAR SOLICITACAO: {e}")
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'mensagem': str(e)}

    # DASHBOARD DOADOR
    def obter_dados_doador(self):
        """Retorna dados agregados para o painel do doador."""
        try:
            # Verifica se tem usuário na sessão
            usuario_id = self.sessao.get('usuario_id')
            if not usuario_id:
                return {'sucesso': False, 'mensagem': 'Usuário não está logado'}

            id_doador = self.sessao.get('id_doador')
            
            #Tenta recuperar id_doador se não estiver na sessão
            if not id_doador:
                q = "SELECT id_doador FROM doador WHERE id_usuario = %s"
                r = self.db.buscar_um(q, (usuario_id,))
                if r:
                    id_doador = r['id_doador']
                    Routes._sessao_global['id_doador'] = id_doador
                    print(f"id_doador recuperado: {id_doador}")

            if not id_doador:
                return {'sucesso': False, 'mensagem': 'Doador não encontrado. Complete seu cadastro.'}

            #Busca dados básicos do doador
            doador = self.db.buscar_um("""
                SELECT 
                    u.nome, 
                    u.email, 
                    d.id_doador,
                    d.razao_social,
                    d.cnpj,
                    cd.descricao_classificacao as classificacao
                FROM usuario u 
                JOIN doador d ON d.id_usuario = u.id_usuario
                LEFT JOIN classificacao_doador cd ON d.id_classificacao = cd.id_classificacao
                WHERE d.id_doador = %s
            """, (id_doador,))

            if not doador:
                return {'sucesso': False, 'mensagem': 'Doador não encontrado'}

            print(f"Buscando dados do doador id={id_doador}")

            #TOTAL DOADO = Soma da quantidade INICIAL de todos os créditos criados
            #Nota: quantidade_disponivel_kwh diminui conforme distribui, por isso usamos ela como "total doado"
            #(assumindo que no momento da criação, quantidade_disponivel = quantidade_inicial)
            query_total_doado = """
                SELECT COALESCE(
                    SUM(
                        c.quantidade_disponivel_kwh + 
                        COALESCE(
                            (SELECT SUM(t.quantidade_kwh)
                             FROM transacao t
                             JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
                             WHERE t.id_credito = c.id_credito 
                               AND st.descricao_status = 'CONCLUIDA'),
                            0
                        )
                    ), 0
                ) as total
                FROM credito c
                WHERE c.id_doador = %s
            """
            result_doado = self.db.buscar_um(query_total_doado, (id_doador,))
            total_doado = float(result_doado['total']) if result_doado else 0.0

            #TOTAL DISTRIBUÍDO = Soma de TODAS as transações CONCLUÍDAS deste doador
            query_distribuido = """
                SELECT COALESCE(SUM(t.quantidade_kwh), 0) as total
                FROM transacao t
                JOIN credito c ON t.id_credito = c.id_credito
                JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
                WHERE c.id_doador = %s 
                  AND st.descricao_status = 'CONCLUIDA'
            """
            result_distribuido = self.db.buscar_um(query_distribuido, (id_doador,))
            total_distribuido = float(result_distribuido['total']) if result_distribuido else 0.0

            #FAMÍLIAS ATENDIDAS = Número ÚNICO de beneficiários que receberam créditos
            query_familias = """
                SELECT COUNT(DISTINCT t.id_beneficiario) as total
                FROM transacao t
                JOIN credito c ON t.id_credito = c.id_credito
                JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
                WHERE c.id_doador = %s 
                  AND st.descricao_status = 'CONCLUIDA'
            """
            result_familias = self.db.buscar_um(query_familias, (id_doador,))
            familias_atendidas = int(result_familias['total']) if result_familias else 0

            #CO2 REDUZIDO = Total distribuído * fator de conversão (0.356 kg CO2/kWh é uma estimativa comum)
            co2_reduzido = round(total_distribuido * 0.356, 2)

            #HISTÓRICO DE CRÉDITOS (últimos 10)
            query_creditos = """
                SELECT 
                    c.id_credito,
                    c.quantidade_disponivel_kwh,
                    c.data_expiracao,
                    sc.descricao_status,
                    -- Calcula quanto foi consumido deste crédito
                    (
                        SELECT COALESCE(SUM(t.quantidade_kwh), 0)
                        FROM transacao t
                        JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
                        WHERE t.id_credito = c.id_credito 
                          AND st.descricao_status = 'CONCLUIDA'
                    ) as quantidade_consumida
                FROM credito c
                JOIN status_credito sc ON c.id_status_credito = sc.id_status_credito
                WHERE c.id_doador = %s
                ORDER BY c.id_credito DESC
                LIMIT 10
            """
            creditos = self.db.buscar_todos(query_creditos, (id_doador,))

            #Adiciona campo quantidade_inicial calculado (disponível + consumido)
            for credito in creditos:
                qtd_disponivel = float(credito['quantidade_disponivel_kwh'] or 0)
                qtd_consumida = float(credito['quantidade_consumida'] or 0)
                credito['quantidade_inicial'] = round(qtd_disponivel + qtd_consumida, 2)

            print(f"Dados carregados: doado={total_doado}, distribuído={total_distribuido}, famílias={familias_atendidas}")

            return {
                'sucesso': True,
                'dados': {
                    'nome': doador['nome'],
                    'email': doador['email'],
                    'razao_social': doador.get('razao_social'),  
                    'cnpj': doador.get('cnpj'),                  
                    'classificacao': doador.get('classificacao'), 
                    'total_doado_kwh': round(total_doado, 2),
                    'total_distribuido_kwh': round(total_distribuido, 2),
                    'familias_atendidas': familias_atendidas,
                    'co2_reduzido_kg': co2_reduzido,
                    'creditos': creditos
                }
            }

        except Exception as e:
            print(f"ERRO OBTER DADOS DOADOR: {e}")
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'mensagem': str(e)}

    #Cria um crédito para o doador e tenta disparar a distribuição.
    def criar_doacao(self, dados):
        try:
            usuario_id = self.sessao.get('usuario_id')
            id_doador = self.sessao.get('id_doador')

            if not usuario_id:
                return {'sucesso': False, 'mensagem': 'Usuário não autenticado'}

            # garante id_doador
            if not id_doador:
                q = "SELECT id_doador FROM doador WHERE id_usuario = %s"
                r = self.db.buscar_um(q, (usuario_id,))
                if r:
                    id_doador = r['id_doador']
                    Routes._sessao_global['id_doador'] = id_doador
                else:
                    id_doador = self.db.criar_doador(usuario_id)
                    Routes._sessao_global['id_doador'] = id_doador

            quantidade = float(dados.get('quantidade_kwh', 0))
            if quantidade <= 0:
                return {'sucesso': False, 'mensagem': 'Quantidade inválida'}

            # Cria crédito
            id_credito = self.db.criar_credito(id_doador=id_doador, quantidade_kwh=quantidade)

            # Log
            self.db.registrar_log_auditoria(id_usuario=usuario_id, tipo_acao='DOACAO', detalhes=f'Criação de crédito id={id_credito} q={quantidade}')

            # Tenta distribuir automaticamente
            try:
                resultado = self.db.executar_distribuicao(limite=10)
            except Exception as e:
                print(f"⚠️ Distribuição automática falhou ao criar doação: {e}")
                resultado = {'mensagem': 'Distribuição falhou', 'error': str(e)}

            return {'sucesso': True, 'mensagem': f'Doação registrada ({quantidade} kWh).', 'distribuicao': resultado}

        except Exception as e:
            print(f"ERRO CRIAR DOACAO: {e}")
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'mensagem': str(e)}
    
    # UTILITÁRIOS
    def verificar_perfil_completo(self, usuario_id, tipo_usuario):
        #Verifica se perfil está completo.
        try:
            if tipo_usuario == 'BENEFICIARIO':
                query = """
                    SELECT b.id_beneficiario, b.id_renda, b.id_consumo, b.num_moradores
                    FROM beneficiario b
                    WHERE b.id_usuario = %s
                """
                result = self.db.buscar_um(query, (usuario_id,))
                return bool(
                    result and 
                    result['id_renda'] and 
                    result['id_consumo'] and 
                    result['num_moradores']
                )
            
            elif tipo_usuario == 'DOADOR':
                query = """
                    SELECT d.id_doador, d.cnpj, d.razao_social
                    FROM doador d
                    WHERE d.id_usuario = %s
                """
                result = self.db.buscar_um(query, (usuario_id,))
                # Para pessoa física não exigimos CNPJ/razão social
                return bool(result and result['id_doador'])
            
            return False  # Se não tem tipo definido, não está completo
            
        except Exception as e:
            print(f"Erro ao verificar perfil: {str(e)}")
            return False

    def definir_tipo_perfil(self, tipo_perfil: str):
        """
            Define o tipo de perfil do usuário (DOADOR ou BENEFICIARIO) e persiste no banco.
            Retorna dict com sucesso e redirect para completar cadastro.
        """
        try:
            usuario_id = self.sessao.get('usuario_id')
            if not usuario_id:
                return {'sucesso': False, 'mensagem': 'Usuário não autenticado'}

            # Atualiza a coluna id_tipo do usuário para o tipo desejado
            query = """
                UPDATE usuario
                SET id_tipo = (
                    SELECT id_tipo FROM tipo_usuario WHERE descricao_tipo = %s
                )
                WHERE id_usuario = %s
            """
            self.db.executar(query, (tipo_perfil, usuario_id))

            # Atualiza sessão global
            Routes._sessao_global['tipo'] = tipo_perfil
            self.sessao = Routes._sessao_global.copy()

            return {'sucesso': True, 'mensagem': 'Perfil definido', 'redirect': '/completar-cadastro'}
        except Exception as e:
            print(f"ERRO definir_tipo_perfil: {e}")
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'mensagem': str(e)}

    def completar_cadastro_doador(self, dados):
        """Finaliza cadastro do doador: cria/atualiza registro em doador com campos adicionais."""
        try:
            usuario_id = self.sessao.get('usuario_id')
            if not usuario_id:
                return {'sucesso': False, 'mensagem': 'Usuário não autenticado'}

            classificacao = dados.get('classificacao', 'PESSOA_FISICA')
            razao_social = dados.get('razao_social')
            cnpj = dados.get('cnpj')

            # Verifica se já existe doador
            row = self.db.buscar_um("SELECT id_doador FROM doador WHERE id_usuario = %s", (usuario_id,))
            if row:
                id_doador = row['id_doador']
            else:
                id_doador = self.db.criar_doador(usuario_id, classificacao)

            # Atualiza campos adicionais
            updates = []
            params = []
            if razao_social:
                updates.append('razao_social = %s')
                params.append(razao_social)
            if cnpj:
                updates.append('cnpj = %s')
                params.append(cnpj)

            if updates:
                query = f"UPDATE doador SET {', '.join(updates)} WHERE id_doador = %s"
                params.append(id_doador)
                self.db.executar(query, tuple(params))

            # Atualiza sessão
            Routes._sessao_global['id_doador'] = id_doador
            self.sessao = Routes._sessao_global.copy()

            self.db.registrar_log_auditoria(id_usuario=usuario_id, tipo_acao='CADASTRO', detalhes=f'Cadastro doador id={id_doador}')

            return {'sucesso': True, 'mensagem': 'Cadastro doador completo', 'redirect': '/painel-doador'}
        except Exception as e:
            print(f"ERRO completar_cadastro_doador: {e}")
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'mensagem': str(e)}
    
    def estatisticas_gerais(self):
        """Retorna estatísticas para página inicial."""
        return {
            "familias_atendidas": 850,
            "total_kwh": 1200000.0
        }
    
    # CRUD: EDITAR / EXCLUIR SOLICITAÇÃO (BENEFICIÁRIO)
    def editar_solicitacao(self, dados):
        """
            Edita uma solicitação na fila (só enquanto AGUARDANDO).
            REGRA: Atualiza data_entrada para NOW(), jogando para o final da fila.
        """
        try:
            usuario_id = self.sessao.get('usuario_id')
            id_benef = self.sessao.get('id_beneficiario')
            if not usuario_id or not id_benef:
                return {'sucesso': False, 'mensagem': 'Usuário não autenticado'}

            id_fila_raw = dados.get('id_fila')
            nova_qtd_raw = dados.get('quantidade_kwh')

            if id_fila_raw is None:
                return {'sucesso': False, 'mensagem': 'ID da fila não informado'}
        
            if nova_qtd_raw is None:
                return {'sucesso': False, 'mensagem': 'Quantidade não informada'}
        
            #Converte para os tipos corretos APÓS validação
            try:
                id_fila = int(id_fila_raw)
                nova_qtd = float(nova_qtd_raw)
            except (ValueError, TypeError) as e:
                return {'sucesso': False, 'mensagem': f'Dados inválidos: {str(e)}'}
        
            if nova_qtd <= 0:
                return {'sucesso': False, 'mensagem': 'Quantidade deve ser maior que zero'}

            # Busca dados do beneficiário para recalcular prioridade
            benef = self.db.buscar_um("""
                SELECT b.num_moradores, rb.valor_renda
                FROM beneficiario b
                LEFT JOIN renda_beneficiario rb ON b.id_renda = rb.id_renda
                WHERE b.id_beneficiario = %s
            """, (id_benef,))

            if not benef:
                return {'sucesso': False, 'mensagem': 'Beneficiário não encontrado'}
                
            #Busca consumo médio atual para validação
            consumo_info = self.db.buscar_um("""
                SELECT cb.media_kwh 
                FROM beneficiario b
                JOIN consumo_beneficiario cb ON b.id_consumo = cb.id_consumo
                WHERE b.id_beneficiario = %s
            """, (id_benef,))
            
            consumo_medio = float(consumo_info.get('media_kwh', 0)) if consumo_info else 0
            if consumo_medio > 0 and nova_qtd_raw > consumo_medio:
                return {
                    'sucesso': False, 
                    'mensagem': f'Você só pode solicitar até {consumo_medio} kWh (seu consumo médio mensal)'
                }

            num_moradores = int(benef.get('num_moradores', 1))
            renda = float(benef.get('valor_renda', 0))

            # Verifica se a solicitação existe e pertence ao beneficiário
            row = self.db.buscar_um("""
                SELECT f.id_fila, f.id_beneficiario, sf.descricao_status_fila
                FROM fila_espera f
                JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila
                WHERE f.id_fila = %s
            """, (id_fila,))

            if not row:
                return {'sucesso': False, 'mensagem': 'Solicitação não encontrada'}
            if row['id_beneficiario'] != id_benef:
                return {'sucesso': False, 'mensagem': 'Permissão negada'}
            if row['descricao_status_fila'] != 'AGUARDANDO':
                return {'sucesso': False, 'mensagem': 'Só é possível editar solicitações enquanto estiverem aguardando.'}

            # Recalcula prioridade
            pri = self.db.buscar_um("SELECT calcular_prioridade(%s, %s, %s, 0) AS prioridade", (renda, nova_qtd, num_moradores))
            prioridade = pri['prioridade'] if pri else 0

            #CRÍTICO: Atualiza data_entrada para NOW() (joga para o final da fila)
            self.db.executar(
                """
                UPDATE fila_espera
                SET consumo_medio_kwh = %s, 
                    num_moradores = %s, 
                    renda_familiar = %s, 
                    prioridade = %s, 
                    data_entrada = NOW()
                WHERE id_fila = %s
                """,
                (nova_qtd, num_moradores, renda, prioridade, id_fila)
            )

            self.db.registrar_log_auditoria(
                id_usuario=usuario_id, 
                tipo_acao='EDITAR_SOLICITACAO', 
                detalhes=f'id_fila={id_fila} nova_qtd={nova_qtd}'
            )

            # Força commit
            try:
                self.db.conn.commit()
            except Exception:
                try:
                    self.db.conn.rollback()
                except Exception:
                    pass

            return {'sucesso': True, 'mensagem': 'Solicitação atualizada! Você foi reposicionado no final da fila.'}

        except Exception as e:
            print(f"ERRO editar_solicitacao: {e}")
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'mensagem': str(e)}

    def excluir_solicitacao(self, dados):
        """
        Exclui (cancela) uma solicitação na fila se ainda estiver AGUARDANDO.
        """
        try:
            usuario_id = self.sessao.get('usuario_id')
            id_benef = self.sessao.get('id_beneficiario')
            if not usuario_id or not id_benef:
                return {'sucesso': False, 'mensagem': 'Usuário não autenticado'}

            id_fila = int(dados.get('id_fila', 0))

            row = self.db.buscar_um("""
                SELECT f.id_fila, f.id_beneficiario, sf.descricao_status_fila
                FROM fila_espera f
                JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila
                WHERE f.id_fila = %s
            """, (id_fila,))

            if not row:
                return {'sucesso': False, 'mensagem': 'Solicitação não encontrada'}
            if row['id_beneficiario'] != id_benef:
                return {'sucesso': False, 'mensagem': 'Permissão negada'}
            if row['descricao_status_fila'] != 'AGUARDANDO':
                return {'sucesso': False, 'mensagem': 'Só é possível excluir solicitações que estejam aguardando.'}

            self.db.executar("DELETE FROM fila_espera WHERE id_fila = %s", (id_fila,))
            self.db.registrar_log_auditoria(
                id_usuario=usuario_id, 
                tipo_acao='EXCLUIR_SOLICITACAO', 
                detalhes=f'id_fila={id_fila}'
            )

            try:
                self.db.conn.commit()
            except Exception:
                try:
                    self.db.conn.rollback()
                except Exception:
                    pass

            return {'sucesso': True, 'mensagem': 'Solicitação cancelada com sucesso'}

        except Exception as e:
            print(f"ERRO excluir_solicitacao: {e}")
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'mensagem': str(e)}

    # CRUD: EDITAR / EXCLUIR DOAÇÃO (DOADOR)
    def editar_doacao(self, dados):
        """
        Permite editar um crédito (quantidade) somente se NÃO houve transações vinculadas.
        """
        try:
            usuario_id = self.sessao.get('usuario_id')
            id_doador = self.sessao.get('id_doador')
            if not usuario_id or not id_doador:
                return {'sucesso': False, 'mensagem': 'Usuário não autenticado'}

            id_credito = int(dados.get('id_credito', 0))
            nova_qtd = float(dados.get('quantidade_kwh', 0))

            row = self.db.buscar_um("SELECT id_doador FROM credito WHERE id_credito = %s", (id_credito,))
            if not row:
                return {'sucesso': False, 'mensagem': 'Crédito não encontrado'}
            if row['id_doador'] != id_doador:
                return {'sucesso': False, 'mensagem': 'Permissão negada'}

            #Verifica se já houve transações
            trans = self.db.buscar_um("SELECT COUNT(*) as cnt FROM transacao WHERE id_credito = %s", (id_credito,))
            if trans and int(trans['cnt']) > 0:
                return {'sucesso': False, 'mensagem': 'Não é possível editar uma doação que já foi distribuída.'}

            self.db.executar("UPDATE credito SET quantidade_disponivel_kwh = %s WHERE id_credito = %s", (nova_qtd, id_credito))
            self.db.registrar_log_auditoria(
                id_usuario=usuario_id, 
                tipo_acao='EDITAR_DOACAO', 
                detalhes=f'id_credito={id_credito} nova_qtd={nova_qtd}'
            )

            try:
                self.db.conn.commit()
            except Exception:
                try:
                    self.db.conn.rollback()
                except Exception:
                    pass

            return {'sucesso': True, 'mensagem': 'Doação atualizada com sucesso'}

        except Exception as e:
            print(f"ERRO editar_doacao: {e}")
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'mensagem': str(e)}

    def excluir_doacao(self, dados):
        """
        Exclui um crédito se NÃO houver transações vinculadas.
        """
        try:
            usuario_id = self.sessao.get('usuario_id')
            id_doador = self.sessao.get('id_doador')
            if not usuario_id or not id_doador:
                return {'sucesso': False, 'mensagem': 'Usuário não autenticado'}

            id_credito = int(dados.get('id_credito', 0))

            row = self.db.buscar_um("SELECT id_doador FROM credito WHERE id_credito = %s", (id_credito,))
            if not row:
                return {'sucesso': False, 'mensagem': 'Crédito não encontrado'}
            if row['id_doador'] != id_doador:
                return {'sucesso': False, 'mensagem': 'Permissão negada'}

            trans = self.db.buscar_um("SELECT COUNT(*) as cnt FROM transacao WHERE id_credito = %s", (id_credito,))
            if trans and int(trans['cnt']) > 0:
                return {'sucesso': False, 'mensagem': 'Não é possível excluir uma doação que já foi distribuída.'}

            # Remove histórico e crédito
            self.db.executar("DELETE FROM historico_credito WHERE id_credito = %s", (id_credito,))
            self.db.executar("DELETE FROM credito WHERE id_credito = %s", (id_credito,))
            self.db.registrar_log_auditoria(
                id_usuario=usuario_id, 
                tipo_acao='EXCLUIR_DOACAO', 
                detalhes=f'id_credito={id_credito}'
            )

            try:
                self.db.conn.commit()
            except Exception:
                try:
                    self.db.conn.rollback()
                except Exception:
                    pass

            return {'sucesso': True, 'mensagem': 'Doação excluída com sucesso'}

        except Exception as e:
            print(f"ERRO excluir_doacao: {e}")
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'mensagem': str(e)}