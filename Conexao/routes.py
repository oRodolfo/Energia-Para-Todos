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
            tipo_usuario = (usuario.get('tipo_usuario') or '').upper()
            if tipo_usuario == 'BENEFICIARIO':
                redirect = '/painel-beneficiario'
                mensagem_final = 'Login realizado com sucesso!'
            elif 'ADMIN' in tipo_usuario or tipo_usuario == 'ADMINISTRADOR':
                # Administradores vão para o CRUD/painel administrativo
                redirect = '/crud'
                mensagem_final = 'Login realizado com sucesso! Cadastro administrativo já está completo.'
            else:
                redirect = '/painel-doador'
                mensagem_final = 'Login realizado com sucesso!'
            print(f"Sessão global após login: {Routes._sessao_global}")
            self.sessao = Routes._sessao_global.copy()

            return {
                'sucesso': True,
                'mensagem': mensagem_final,
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
            # Garantia explícita: o cadastro inicial NÃO utiliza telefone.
            Routes._sessao_global.pop('telefone', None)
            Routes._sessao_global.pop('id_telefone', None)

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

            # Assegura tipo e vínculo em sessão global
            Routes._sessao_global['id_beneficiario'] = id_beneficiario
            Routes._sessao_global['tipo'] = 'BENEFICIARIO'
            self.sessao = Routes._sessao_global.copy()

            # Garante que o usuário no banco tenha id_tipo correto (caso não tenha sido definido antes)
            try:
                self.db.executar("""
                    UPDATE usuario
                    SET id_tipo = (
                        SELECT id_tipo FROM tipo_usuario WHERE descricao_tipo = %s
                    )
                    WHERE id_usuario = %s
                """, ('BENEFICIARIO', usuario_id))
            except Exception:
                print('Aviso: não foi possível atualizar id_tipo do usuário para BENEFICIARIO no banco')

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
    
            #Total recebido APENAS de solicitações ATENDIDAS na fila
            query_total = """
                SELECT COALESCE(SUM(f.consumo_medio_kwh), 0) AS total_recebido
                FROM fila_espera f
                JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila
                WHERE f.id_beneficiario = %s
                    AND sf.descricao_status_fila = 'ATENDIDO'
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
    
            # ✅ Busca dados do beneficiário
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
    
            # ✅ CORREÇÃO CRÍTICA: Calcula total APENAS de solicitações ATIVAS no mês
            query_total_mes = """
                SELECT COALESCE(SUM(f.consumo_medio_kwh), 0) as total_solicitado_mes
                FROM fila_espera f
                JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila
                WHERE f.id_beneficiario = %s
                    AND EXTRACT(MONTH FROM f.data_entrada) = EXTRACT(MONTH FROM CURRENT_DATE)
                    AND EXTRACT(YEAR FROM f.data_entrada) = EXTRACT(YEAR FROM CURRENT_DATE)
                    AND sf.descricao_status_fila IN ('AGUARDANDO', 'ATENDIDO')
            """
            result_mes = self.db.buscar_um(query_total_mes, (id_beneficiario,))
            total_ja_solicitado = float(result_mes['total_solicitado_mes']) if result_mes else 0
    
            # ✅ Calcula quanto ainda pode solicitar
            disponivel_para_solicitar = consumo_medio - total_ja_solicitado
    
            print(f"📊 Consumo médio: {consumo_medio} kWh")
            print(f"📊 Já solicitado este mês (ATIVO): {total_ja_solicitado} kWh")
            print(f"📊 Disponível para solicitar: {disponivel_para_solicitar} kWh")
            print(f"📊 Quantidade solicitada agora: {quantidade_solicitada} kWh")
    
            # ✅ VALIDAÇÃO 1: Verifica se já atingiu o limite mensal
            if disponivel_para_solicitar <= 0:
                return {
                    'sucesso': False,
                    'mensagem': f'Você já solicitou todo seu consumo médio mensal ({consumo_medio} kWh). Aguarde o próximo mês para novas solicitações.'
                }
    
            # ✅ VALIDAÇÃO 2: Verifica se nova solicitação ultrapassa limite disponível
            if quantidade_solicitada > disponivel_para_solicitar:
                return {
                    'sucesso': False,
                    'mensagem': f'Você só pode solicitar até {disponivel_para_solicitar:.2f} kWh. Já solicitou {total_ja_solicitado:.2f} kWh dos seus {consumo_medio} kWh mensais.'
                }
    
            # ✅ VALIDAÇÃO 3: Verifica se já está na fila AGUARDANDO (não permite duplicatas)
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
                    'mensagem': 'Você já possui uma solicitação aguardando. Aguarde o atendimento ou cancele a anterior.'
                }
    
            # ✅ Insere na fila
            self.db.entrar_na_fila(
                id_beneficiario=id_beneficiario,
                renda_familiar=float(benef_dados['valor_renda'] or 0),
                consumo_medio_kwh=quantidade_solicitada,
                num_moradores=int(benef_dados['num_moradores'] or 1)
            )
    
            mensagem = f'Solicitação de {quantidade_solicitada} kWh registrada! Você entrou na fila.'
    
            # ✅ Tenta distribuição
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
        
    def obter_meu_perfil(self):
        """Retorna dados básicos do usuário logado para edição de perfil."""
        try:
            usuario_id = self.sessao.get('usuario_id')
            if not usuario_id:
                return {'sucesso': False, 'mensagem': 'Usuário não autenticado'}
    
            query = """
                SELECT u.id_usuario, u.nome, u.email
                FROM usuario u
                WHERE u.id_usuario = %s
            """
            dados = self.db.buscar_um(query, (usuario_id,))
    
            if not dados:
                return {'sucesso': False, 'mensagem': 'Usuário não encontrado'}

            # Retorna também informações de sessão essenciais para a UI (tipo e vínculos)
            tipo = self.sessao.get('tipo')
            id_doador = self.sessao.get('id_doador')
            id_beneficiario = self.sessao.get('id_beneficiario')

            return {
                'sucesso': True,
                'dados': {
                    'id_usuario': dados['id_usuario'],
                    'nome': dados['nome'],
                    'email': dados['email']
                },
                # Campos no nível superior para compatibilidade com FrontEnd
                'tipo': tipo,
                'id_doador': id_doador,
                'id_beneficiario': id_beneficiario
            }
        except Exception as e:
            print(f"ERRO obter_meu_perfil: {e}")
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
            # Administradores não precisam completar perfil adicional
            if tipo_usuario and ('ADMIN' in tipo_usuario.upper() or tipo_usuario.upper() == 'ADMINISTRADOR'):
                return True
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
            # Assegura tipo e vínculo em sessão global
            Routes._sessao_global['id_doador'] = id_doador
            Routes._sessao_global['tipo'] = 'DOADOR'
            self.sessao = Routes._sessao_global.copy()

            # Garante que o usuário no banco tenha id_tipo correto (caso não tenha sido definido antes)
            try:
                self.db.executar("""
                    UPDATE usuario
                    SET id_tipo = (
                        SELECT id_tipo FROM tipo_usuario WHERE descricao_tipo = %s
                    )
                    WHERE id_usuario = %s
                """, ('DOADOR', usuario_id))
            except Exception:
                # Não fatal: se houver problema ao persistir, logamos e continuamos (sessão já atualizada)
                print('Aviso: não foi possível atualizar id_tipo do usuário para DOADOR no banco')

            self.db.registrar_log_auditoria(id_usuario=usuario_id, tipo_acao='CADASTRO', detalhes=f'Cadastro doador id={id_doador}')

            return {'sucesso': True, 'mensagem': 'Cadastro doador completo', 'redirect': '/painel-doador'}
        except Exception as e:
            print(f"ERRO completar_cadastro_doador: {e}")
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'mensagem': str(e)}
    
    def estatisticas_gerais(self):
        """Retorna estatísticas reais do banco de dados para página inicial."""
        try:
            # Total distribuído = Soma de todas transações CONCLUÍDAS
            query_kwh = """
                SELECT COALESCE(SUM(t.quantidade_kwh), 0) AS total_kwh
                FROM transacao t
                JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
                WHERE st.descricao_status = 'CONCLUIDA'
            """
            result_kwh = self.db.buscar_um(query_kwh)
            total_kwh = float(result_kwh['total_kwh']) if result_kwh else 0.0
        
            # Famílias atendidas = Número ÚNICO de beneficiários que receberam créditos
            query_familias = """
                SELECT COUNT(DISTINCT t.id_beneficiario) AS total_familias
                FROM transacao t
                JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
                WHERE st.descricao_status = 'CONCLUIDA'
            """
            result_familias = self.db.buscar_um(query_familias)
            total_familias = int(result_familias['total_familias']) if result_familias else 0
        
            print(f"📊 Estatísticas gerais: {total_kwh} kWh distribuídos, {total_familias} famílias atendidas")
        
            return {
                "total_kwh": round(total_kwh, 2),
                "familias_atendidas": total_familias
            }
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas gerais: {e}")
            import traceback
            traceback.print_exc()
            # Retorna valores padrão em caso de erro
            return {
                "total_kwh": 0.0,
                "familias_atendidas": 0
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

            # VALIDAÇÃO E CONVERSÃO SEGURA DOS DADOS
            id_fila_raw = dados.get('id_fila')
            nova_qtd_raw = dados.get('quantidade_kwh')

            if id_fila_raw is None:
                return {'sucesso': False, 'mensagem': 'ID da fila não informado'}
        
            if nova_qtd_raw is None:
                return {'sucesso': False, 'mensagem': 'Quantidade não informada'}
        
            try:
                id_fila = int(id_fila_raw)
                nova_qtd = float(nova_qtd_raw)
            except (ValueError, TypeError) as e:
                return {'sucesso': False, 'mensagem': f'Dados inválidos: {str(e)}'}
        
            if nova_qtd <= 0:
                return {'sucesso': False, 'mensagem': 'Quantidade deve ser maior que zero'}

            # Busca dados do beneficiário
            benef = self.db.buscar_um("""
                SELECT b.num_moradores, rb.valor_renda, cb.media_kwh
                FROM beneficiario b
                LEFT JOIN renda_beneficiario rb ON b.id_renda = rb.id_renda
                LEFT JOIN consumo_beneficiario cb ON b.id_consumo = cb.id_consumo
                WHERE b.id_beneficiario = %s
            """, (id_benef,))

            if not benef:
                return {'sucesso': False, 'mensagem': 'Beneficiário não encontrado'}
        
            renda_familiar = float(benef.get('valor_renda') or 0)
            consumo_medio = float(benef.get('media_kwh') or 0)
            num_moradores = int(benef.get('num_moradores') or 1)

            # Calcula total EXCETO a solicitação atual
            query_total_mes = """
                SELECT COALESCE(SUM(f.consumo_medio_kwh), 0) as total_mes
                FROM fila_espera f
                JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila
                WHERE f.id_beneficiario = %s
                    AND EXTRACT(MONTH FROM f.data_entrada) = EXTRACT(MONTH FROM CURRENT_DATE)
                    AND EXTRACT(YEAR FROM f.data_entrada) = EXTRACT(YEAR FROM CURRENT_DATE)
                    AND sf.descricao_status_fila IN ('AGUARDANDO', 'ATENDIDO')
                    AND f.id_fila != %s
            """
            result_mes = self.db.buscar_um(query_total_mes, (id_benef, id_fila))
            total_outras_solicitacoes = float(result_mes['total_mes'] if result_mes else 0)

            # VALIDAÇÃO CORRETA: Soma da NOVA quantidade + outras solicitações
            total_apos_edicao = nova_qtd + total_outras_solicitacoes

            print(f"📊 Consumo médio: {consumo_medio} kWh")
            print(f"📊 Outras solicitações ativas: {total_outras_solicitacoes} kWh")
            print(f"📊 Nova quantidade desta solicitação: {nova_qtd} kWh")
            print(f"📊 Total após edição: {total_apos_edicao} kWh")

            # VALIDAÇÃO: Total após edição não pode ultrapassar consumo médio
            if total_apos_edicao > consumo_medio:
                disponivel = consumo_medio - total_outras_solicitacoes
                return {
                    'sucesso': False, 
                    'mensagem': f'Você só pode solicitar até {disponivel:.2f} kWh nesta solicitação. Já tem {total_outras_solicitacoes:.2f} kWh em outras solicitações. Limite mensal: {consumo_medio} kWh.'
                }

            # Verificação de existência e pertence ao beneficiário (busca segura)
            row = self.db.buscar_um("""
                SELECT f.id_fila, f.id_beneficiario, sf.descricao_status_fila
                FROM fila_espera f
                JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila
                WHERE f.id_fila = %s AND f.id_beneficiario = %s
            """, (id_fila, id_benef))

            if not row:
                return {'sucesso': False, 'mensagem': 'Solicitação não encontrada', 'http_status': 404}

            if row['descricao_status_fila'] != 'AGUARDANDO':
                return {'sucesso': False, 'mensagem': 'Só é possível editar solicitações enquanto estiverem aguardando.', 'http_status': 400}

            # Recálculo de prioridade
            pri = self.db.buscar_um(
                "SELECT calcular_prioridade(%s, %s, %s, 0) AS prioridade", 
                (renda_familiar, nova_qtd, num_moradores)
            )
            prioridade = pri['prioridade'] if pri else 0

            # Atualização
            self.db.executar("""
                UPDATE fila_espera
                SET consumo_medio_kwh = %s, 
                    num_moradores = %s, 
                    renda_familiar = %s, 
                    prioridade = %s, 
                    data_entrada = NOW()
                WHERE id_fila = %s
            """, (nova_qtd, num_moradores, renda_familiar, prioridade, id_fila))

            self.db.registrar_log_auditoria(
                id_usuario=usuario_id, 
                tipo_acao='EDITAR_SOLICITACAO', 
                detalhes=f'id_fila={id_fila} nova_qtd={nova_qtd}'
            )

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

            #CONVERSÃO SEGURA
            try:
                id_fila = int(dados.get('id_fila', 0))
            except (ValueError, TypeError):
                return {'sucesso': False, 'mensagem': 'ID da fila inválido'}

            if id_fila <= 0:
                return {'sucesso': False, 'mensagem': 'ID da fila inválido'}

            # VERIFICAÇÃO: Se existe e pertence ao beneficiário
            # Busca a solicitação garantindo que pertença ao beneficiário
            row = self.db.buscar_um("""
                SELECT f.id_fila, f.id_beneficiario, sf.descricao_status_fila
                FROM fila_espera f
                JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila
                WHERE f.id_fila = %s AND f.id_beneficiario = %s
            """, (id_fila, id_benef))

            if not row:
                return {'sucesso': False, 'mensagem': 'Solicitação não encontrada', 'http_status': 404}

            if row['descricao_status_fila'] != 'AGUARDANDO':
                return {'sucesso': False, 'mensagem': 'Só é possível excluir solicitações que estejam aguardando.', 'http_status': 400}

            # EXCLUSÃO
            self.db.executar("DELETE FROM fila_espera WHERE id_fila = %s", (id_fila,))
        
            #  LOG
            self.db.registrar_log_auditoria(
                id_usuario=usuario_id, 
                tipo_acao='EXCLUIR_SOLICITACAO', 
                detalhes=f'id_fila={id_fila}'
            )

            # COMMIT
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
        
    def atualizar_beneficiario(self, dados):
        """
        Atualiza dados do beneficiário (renda e moradores).
    
        Parâmetros:
        - dados: dict com 'renda_familiar' e 'num_moradores'
    
        Retorna:
        - dict com sucesso True/False
        """
        try:
            usuario_id = self.sessao.get('usuario_id')
            id_beneficiario = self.sessao.get('id_beneficiario')
        
            if not usuario_id or not id_beneficiario:
                return {'sucesso': False, 'mensagem': 'Usuário não autenticado'}
        
            renda_familiar = float(dados.get('renda_familiar', 0))
            num_moradores = int(dados.get('num_moradores', 1))
        
            if num_moradores < 1:
                return {'sucesso': False, 'mensagem': 'Quantidade de moradores deve ser maior que 0'}
        
            # Busca ID da renda atual
            query_renda = "SELECT id_renda FROM beneficiario WHERE id_beneficiario = %s"
            result = self.db.buscar_um(query_renda, (id_beneficiario,))
        
            if not result:
                return {'sucesso': False, 'mensagem': 'Beneficiário não encontrado'}
        
            id_renda = result.get('id_renda')
        
            # Atualizar ou criar renda
            if id_renda:
                self.db.executar(
                    "UPDATE renda_beneficiario SET valor_renda = %s WHERE id_renda = %s",
                    (renda_familiar, id_renda)
                )
            else:
                cursor_renda = self.db.executar(
                    "INSERT INTO renda_beneficiario (valor_renda, periodo) VALUES (%s, 'MENSAL') RETURNING id_renda",
                    (renda_familiar,)
                )
                id_renda = cursor_renda.fetchone()['id_renda']
        
            # Atualizar beneficiário
            self.db.executar(
                "UPDATE beneficiario SET num_moradores = %s, id_renda = %s WHERE id_beneficiario = %s",
                (num_moradores, id_renda, id_beneficiario)
            )
        
            self.db.registrar_log_auditoria(
                id_usuario=usuario_id,
                tipo_acao='EDITAR_PERFIL',
                detalhes=f'Atualização de dados - renda: {renda_familiar}, moradores: {num_moradores}'
            )
        
            return {
                'sucesso': True,
                'mensagem': 'Dados do beneficiário atualizados com sucesso'
            }
    
        except Exception as e:
            print(f"ERRO atualizar_beneficiario: {e}")
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'mensagem': str(e)}
    def solicitar_recuperacao_senha(self, dados):
        """
        Gera código de recuperação para o email informado.
        VALIDAÇÃO: Retorna erro se email não existe
        """
        try:
            email = dados.get('email', '').strip()
    
            if not email:
                return {'sucesso': False, 'mensagem': 'Email é obrigatório'}
    
            # Gera código (retorna None se email não existe ou não está ativo)
            codigo = self.db.gerar_codigo_recuperacao(email)
    
            if codigo:
                #Email existe - código gerado com sucesso
                print(f"\n{'='*50}")
                print(f"CÓDIGO DE RECUPERAÇÃO GERADO")
                print(f"Email: {email}")
                print(f"Código: {codigo}")
                print(f"Válido por: 15 minutos")
                print(f"{'='*50}\n")
        
                return {
                    'sucesso': True,
                    'mensagem': 'Código enviado com sucesso!',
                    'codigo_debug': codigo  # APENAS PARA DESENVOLVIMENTO
                }
            else:
                # Email NÃO existe ou não está ativo
                print(f"⚠️ Tentativa de recuperação para email não cadastrado: {email}")
                return {
                    'sucesso': False,
                    'mensagem': 'Email não encontrado. Verifique se está cadastrado no sistema.'
                }
        
        except Exception as e:
            print(f"Erro ao solicitar recuperação: {e}")
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'mensagem': 'Erro ao processar solicitação'}

    def validar_codigo_recuperacao(self, dados):
        """
        Valida código informado pelo usuário.
        """
        try:
            email = dados.get('email', '').strip()
            codigo = dados.get('codigo', '').strip()
        
            if not email or not codigo:
                return {'sucesso': False, 'mensagem': 'Email e código são obrigatórios'}
        
            status = self.db.validar_codigo_recuperacao(email, codigo)
            # status pode ser 'OK', 'EXPIRADO', 'INVALIDO'
            if status == 'OK':
                return {'sucesso': True, 'mensagem': 'Código válido', 'status': 'OK'}
            elif status == 'EXPIRADO':
                return {
                    'sucesso': False,
                    'mensagem': 'Código expirado. Clique em solicitar novo código.',
                    'status': 'EXPIRADO'
                }
            else:
                return {
                    'sucesso': False,
                    'mensagem': 'Código inválido. Verifique e tente novamente.',
                    'status': 'INVALIDO'
                }
            
        except Exception as e:
            print(f"Erro ao validar código: {e}")
            return {'sucesso': False, 'mensagem': str(e)}

    def resetar_senha_com_codigo(self, dados):
        """
        Reseta senha após validação de código.
        """
        try:
            email = dados.get('email', '').strip()
            nova_senha = dados.get('nova_senha', '')
        
            if not email or not nova_senha:
                return {'sucesso': False, 'mensagem': 'Todos os campos são obrigatórios'}
        
            # Valida força da senha (mesma validação do cadastro)
            if len(nova_senha) < 8:
                return {'sucesso': False, 'mensagem': 'Senha deve ter no mínimo 8 caracteres'}
        
            if self.db.resetar_senha(email, nova_senha):
                self.db.registrar_log_auditoria(
                    id_usuario=None,
                    tipo_acao='RECUPERACAO_SENHA',
                    detalhes=f'Senha resetada para {email}'
                )
            
                return {
                    'sucesso': True,
                    'mensagem': 'Senha alterada com sucesso!',
                    'redirect': '/login'
                }
            else:
                return {'sucesso': False, 'mensagem': 'Erro ao resetar senha'}
            
        except Exception as e:
            print(f"Erro ao resetar senha: {e}")
            return {'sucesso': False, 'mensagem': str(e)}    
    
    # ============================================
    # ROTAS ADMINISTRATIVAS
    # ============================================
    def obter_metricas_admin(self):
        """Retorna métricas gerais do sistema para o dashboard admin."""
        try:
            query = """
                SELECT 
                    (SELECT COUNT(*) FROM usuario) as total_usuarios,
                    (SELECT COUNT(*) FROM doador) as total_doadores,
                    (SELECT COUNT(*) FROM beneficiario) as total_beneficiarios,
                    COALESCE(SUM(CASE WHEN sc.descricao_status = 'DISPONIVEL' THEN c.quantidade_disponivel_kwh ELSE 0 END), 0) as creditos_disponiveis,
                    COALESCE(SUM(CASE WHEN sc.descricao_status != 'DISPONIVEL' THEN c.quantidade_disponivel_kwh ELSE 0 END), 0) as creditos_distribuidos,
                    (SELECT COUNT(*) FROM fila_espera f JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila WHERE sf.descricao_status_fila = 'AGUARDANDO') as beneficiarios_na_fila,
                    (SELECT COUNT(*) FROM log_auditoria WHERE DATE(data_hora) = CURRENT_DATE) as atividades_24h
                FROM credito c
                LEFT JOIN status_credito sc ON c.id_status_credito = sc.id_status_credito
            """
            metricas = self.db.buscar_um(query)
            
            return {
                'sucesso': True,
                'metricas': metricas or {
                    'total_usuarios': 0,
                    'total_doadores': 0,
                    'total_beneficiarios': 0,
                    'creditos_disponiveis': 0,
                    'creditos_distribuidos': 0,
                    'beneficiarios_na_fila': 0,
                    'atividades_24h': 0
                }
            }
        except Exception as e:
            print(f"Erro ao obter métricas: {e}")
            return {'sucesso': False, 'mensagem': str(e)}

    def listar_beneficiarios_admin(self):
        """Lista todos os beneficiários para o admin."""
        try:
            query = """
                SELECT 
                    b.id_beneficiario,
                    b.num_moradores,
                    u.nome,
                    u.email,
                    rb.valor_renda,
                    cb.media_kwh,
                    sb.descricao_status_beneficiario
                FROM beneficiario b
                JOIN usuario u ON b.id_usuario = u.id_usuario
                LEFT JOIN renda_beneficiario rb ON b.id_renda = rb.id_renda
                LEFT JOIN consumo_beneficiario cb ON b.id_consumo = cb.id_consumo
                LEFT JOIN status_beneficiario sb ON b.id_status_beneficiario = sb.id_status_beneficiario
                ORDER BY b.id_beneficiario DESC
                LIMIT 100
            """
            beneficiarios = self.db.buscar_todos(query)
            
            return {
                'sucesso': True,
                'beneficiarios': beneficiarios or []
            }
        except Exception as e:
            print(f"Erro ao listar beneficiários: {e}")
            return {'sucesso': False, 'mensagem': str(e)}

    def listar_doadores_admin(self):
        """Lista todos os doadores para o admin."""
        try:
            query = """
                SELECT 
                    d.id_doador,
                    d.data_cadastro,
                    u.nome,
                    u.email,
                    cd.descricao_classificacao,
                    COALESCE(
                        (SELECT SUM(c.quantidade_disponivel_kwh + 
                            COALESCE((SELECT SUM(t.quantidade_kwh)
                                      FROM transacao t
                                      JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
                                      WHERE t.id_credito = c.id_credito AND st.descricao_status = 'CONCLUIDA'), 0))
                         FROM credito c
                         WHERE c.id_doador = d.id_doador), 0
                    ) as total_doado
                FROM doador d
                JOIN usuario u ON d.id_usuario = u.id_usuario
                LEFT JOIN classificacao_doador cd ON d.id_classificacao = cd.id_classificacao
                ORDER BY d.id_doador DESC
                LIMIT 100
            """
            doadores = self.db.buscar_todos(query)
            
            return {
                'sucesso': True,
                'doadores': doadores or []
            }
        except Exception as e:
            print(f"Erro ao listar doadores: {e}")
            return {'sucesso': False, 'mensagem': str(e)}

    def listar_creditos_admin(self):
        """Lista todos os créditos para o admin."""
        try:
            query = """
                SELECT 
                    c.id_credito,
                    c.quantidade_disponivel_kwh,
                    c.data_expiracao,
                    sc.descricao_status as status,
                    u.nome as nome_doador,
                    d.id_doador
                FROM credito c
                JOIN status_credito sc ON c.id_status_credito = sc.id_status_credito
                JOIN doador d ON c.id_doador = d.id_doador
                JOIN usuario u ON d.id_usuario = u.id_usuario
                ORDER BY c.id_credito DESC
                LIMIT 100
            """
            creditos = self.db.buscar_todos(query)
            
            return {
                'sucesso': True,
                'creditos': creditos or []
            }
        except Exception as e:
            print(f"Erro ao listar créditos: {e}")
            return {'sucesso': False, 'mensagem': str(e)}

    def listar_fila_admin(self):
        """Lista fila de espera completa para o admin."""
        try:
            query = """
                SELECT 
                    f.id_fila,
                    f.id_beneficiario,
                    u.nome,
                    u.email,
                    f.renda_familiar,
                    f.consumo_medio_kwh,
                    f.data_entrada,
                    f.prioridade,
                    sf.descricao_status_fila as status
                FROM fila_espera f
                JOIN beneficiario b ON f.id_beneficiario = b.id_beneficiario
                JOIN usuario u ON b.id_usuario = u.id_usuario
                JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila
                ORDER BY f.prioridade DESC, f.data_entrada ASC
                LIMIT 100
            """
            fila = self.db.buscar_todos(query)
            
            return {
                'sucesso': True,
                'fila': fila or []
            }
        except Exception as e:
            print(f"Erro ao listar fila: {e}")
            return {'sucesso': False, 'mensagem': str(e)}

    def listar_logs_admin(self, limite=50):
        """Lista logs de auditoria para o admin."""
        try:
            query = """
                SELECT 
                    la.id_log,
                    la.data_hora,
                    la.ip_acesso,
                    la.detalhes,
                    u.nome as nome_usuario,
                    ta.descricao_tipo_acao,
                    sl.descricao_status_log
                FROM log_auditoria la
                LEFT JOIN usuario u ON la.id_usuario = u.id_usuario
                LEFT JOIN tipo_acao ta ON la.id_tipo_acao = ta.id_tipo_acao
                LEFT JOIN status_log sl ON la.id_status_log = sl.id_status_log
                ORDER BY la.data_hora DESC
                LIMIT %s
            """
            logs = self.db.buscar_todos(query, (limite,))
            
            return {
                'sucesso': True,
                'logs': logs or []
            }
        except Exception as e:
            print(f"Erro ao listar logs: {e}")
            return {'sucesso': False, 'mensagem': str(e)}

    def executar_distribuicao_admin(self, limite=10):
        """Executa distribuição de créditos (admin)."""
        try:
            resultado = self.db.executar_distribuicao(limite=limite)
            
            return {
                'sucesso': True,
                'resultado': resultado
            }
        except Exception as e:
            print(f"Erro na distribuição: {e}")
            return {'sucesso': False, 'mensagem': str(e)}

    def obter_estatisticas_sistema(self):
        """Retorna estatísticas gerais do sistema."""
        try:
            query_registros = """
                SELECT 
                    (SELECT COUNT(*) FROM usuario) +
                    (SELECT COUNT(*) FROM credito) +
                    (SELECT COUNT(*) FROM transacao) as total
            """
            total_reg = self.db.buscar_um(query_registros)
            
            query_trans = "SELECT COUNT(*) as total FROM transacao"
            total_trans = self.db.buscar_um(query_trans)
            
            query_logs = "SELECT COUNT(*) as total FROM log_auditoria"
            total_logs = self.db.buscar_um(query_logs)
            
            return {
                'sucesso': True,
                'total_registros': total_reg['total'] if total_reg else 0,
                'total_transacoes': total_trans['total'] if total_trans else 0,
                'total_logs': total_logs['total'] if total_logs else 0
            }
        except Exception as e:
            print(f"Erro ao obter estatísticas: {e}")
            return {'sucesso': False, 'mensagem': str(e)}
        print(f"Erro ao obter estatísticas: {e}")
        return {'sucesso': False, 'mensagem': str(e)}