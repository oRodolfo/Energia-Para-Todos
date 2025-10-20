# --- Caminho absoluto para o BackEnd ---
import os, sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "BackEnd")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from datetime import datetime, timedelta

# ✅ CORREÇÃO 1: Remover "backend." do import
from database import Database

# ✅ CORREÇÃO 2: Importar classes corretas
from models.doador import Doador, ClassificacaoDoador
from models.beneficiario import Beneficiario
from models.credito import Credito
from services.distribuidor_creditos import DistribuidorCreditos
from models.fila_espera import FilaEspera, ItemFila 


class Routes:
    """Rotas simplificadas - apenas nome, sobrenome, email e senha"""
    
    def __init__(self):
        self.db = Database()
        self.sessao = {}
    
    def login(self, dados):
        """Processa login"""
        email = dados.get('email')
        senha = dados.get('password')
        
        usuario = self.db.validar_login(email, senha)
        
        if usuario:
            self.sessao['usuario_id'] = usuario['id_usuario']
            self.sessao['nome'] = usuario['nome']
            self.sessao['email'] = usuario['email']
            self.sessao['tipo'] = usuario['tipo_usuario']
            
            self.db.atualizar_ultimo_login(email)
            
            self.db.registrar_log_auditoria(
                id_usuario=usuario['id_usuario'],
                tipo_acao='LOGIN',
                detalhes=f"Login realizado por {email}"
            )
            
            return {
                'sucesso': True,
                'mensagem': 'Login realizado!',
                'tipo': usuario['tipo_usuario'],
                'redirect': '/'
            }
        else:
            return {
                'sucesso': False,
                'mensagem': 'Email ou senha incorretos'
            }
    
    def cadastro_doador(self, dados):
        """Cadastra doador com APENAS: firstName, lastName, email, password"""
        try:
            # Monta nome completo
            nome_completo = f"{dados.get('firstName', '')} {dados.get('lastName', '')}"
            
            # 1. Criar usuário
            id_usuario = self.db.criar_usuario_simples(
                nome=nome_completo.strip(),
                email=dados['email'],
                senha=dados['password'],
                tipo_usuario='DOADOR'
            )
            
            # 2. Criar doador
            id_doador = self.db.criar_doador(
                id_usuario=id_usuario,
                classificacao='PESSOA_FISICA'
            )
            
            # 3. Log
            self.db.registrar_log_auditoria(
                id_usuario=id_usuario,
                tipo_acao='CADASTRO',
                detalhes=f"Doador cadastrado: {nome_completo}"
            )
            
            # 4. Login automático
            self.sessao['usuario_id'] = id_usuario
            self.sessao['tipo'] = 'DOADOR'
            self.sessao['nome'] = nome_completo
            self.sessao['email'] = dados['email']
            
            return {
                'sucesso': True,
                'mensagem': 'Cadastro realizado com sucesso!',
                'redirect': '/login'
            }
            
        except Exception as e:
            print(f"❌ ERRO CADASTRO DOADOR: {e}")
            return {
                'sucesso': False,
                'mensagem': f'Erro ao cadastrar: {str(e)}'
            }
    
    def dashboard_doador(self):
        """Dashboard do doador"""
        usuario_id = self.sessao.get('usuario_id')
        
        doador_db = self.db.buscar_doador_por_usuario(usuario_id)
        
        if not doador_db:
            return {'erro': 'Doador não encontrado'}
        
        # Converte para POO
        doador_poo = Doador(
            id_doador=doador_db['id_doador'],
            id_usuario=doador_db['id_usuario'],
            nome=doador_db['nome'],
            email=doador_db['email'],
            telefone=doador_db['telefone'],
            cep=doador_db['cep'],
            classificacao=ClassificacaoDoador.PESSOA_FISICA
        )
        
        doador_poo._total_kwh_doados = float(doador_db['total_kwh_doados'])
        doador_poo._total_doacoes = doador_db['total_doacoes']
        
        impacto = doador_poo.calcular_impacto_social(preco_kwh=0.80)
        
        creditos = self.db.listar_creditos_doador(doador_db['id_doador'])
        
        return {
            'doador': {
                'id': doador_db['id_doador'],
                'nome': doador_db['nome'],
                'email': doador_db['email'],
                'classificacao': doador_db['classificacao'],
                'total_kwh_doados': float(doador_db['total_kwh_doados']),
                'total_doacoes': doador_db['total_doacoes']
            },
            'impacto': impacto,
            'creditos': creditos
        }
    
    def criar_doacao(self, dados):
        """Cria doação"""
        usuario_id = self.sessao.get('usuario_id')
        doador_db = self.db.buscar_doador_por_usuario(usuario_id)
        
        if not doador_db:
            return {'sucesso': False, 'mensagem': 'Doador não encontrado'}
        
        try:
            quantidade_kwh = float(dados['quantidade_kwh'])
            meses_validade = int(dados.get('meses_validade', 12))
            data_expiracao = datetime.now() + timedelta(days=meses_validade * 30)
            
            id_credito = self.db.criar_credito(
                id_doador=doador_db['id_doador'],
                quantidade_kwh=quantidade_kwh,
                data_expiracao=data_expiracao
            )
            
            self.db.registrar_historico_credito(id_credito, quantidade_kwh)
            
            self.db.registrar_log_auditoria(
                id_usuario=usuario_id,
                tipo_acao='DOACAO',
                detalhes=f"Doação de {quantidade_kwh} kWh registrada"
            )
            
            return {
                'sucesso': True,
                'mensagem': f'Doação de {quantidade_kwh} kWh registrada!',
                'redirect': '/dashboard'
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'mensagem': f'Erro: {str(e)}'
            }
    
    def distribuir_creditos(self, dados):
        """Distribui créditos usando POO"""
        try:
            num_beneficiarios = int(dados.get('num_beneficiarios', 10))
            
            distribuidor = DistribuidorCreditos()
            
            # Carrega créditos
            creditos_db = self.db.listar_creditos_disponiveis()
            for cred_db in creditos_db:
                cred_poo = Credito(
                    id_credito=cred_db['id_credito'],
                    id_doador=cred_db['id_doador'],
                    quantidade_inicial_kwh=float(cred_db['quantidade_disponivel_kwh']),
                    data_expiracao=cred_db['data_expiracao']
                )
                cred_poo._quantidade_disponivel_kwh = float(cred_db['quantidade_disponivel_kwh'])
                distribuidor.adicionar_credito(cred_poo)
            
            # Cria fila
            fila = FilaEspera(id_temporada=1, nome_temporada="2025")
            
            beneficiarios_db = self.db.listar_beneficiarios_aprovados()
            for ben_db in beneficiarios_db:
                ben_poo = Beneficiario(
                    id_beneficiario=ben_db['id_beneficiario'],
                    id_usuario=ben_db['id_usuario'],
                    nome=ben_db['nome'],
                    email=ben_db['email'],
                    telefone=ben_db['telefone'],
                    cep=ben_db['cep'],
                    renda_familiar=float(ben_db['renda_familiar']),
                    consumo_medio_kwh=float(ben_db['consumo_medio_kwh']),
                    num_moradores=ben_db['num_moradores']
                )
                ben_poo._saldo_creditos_kwh = float(ben_db['saldo_creditos_kwh'])
                fila.adicionar_beneficiario(ben_poo)
            
            # DISTRIBUI
            resultado = distribuidor.distribuir_proporcional(fila, num_beneficiarios)
            
            # Salva no banco
            if resultado['sucesso']:
                for transacao_poo in distribuidor._transacoes:
                    self.db.criar_transacao(
                        id_beneficiario=transacao_poo.id_beneficiario,
                        id_credito=transacao_poo.id_credito,
                        quantidade_kwh=transacao_poo.quantidade_kwh,
                        tipo_movimento='DISTRIBUICAO'
                    )
                    
                    for cred_db in creditos_db:
                        if cred_db['id_credito'] == transacao_poo.id_credito:
                            nova_qtd = float(cred_db['quantidade_disponivel_kwh']) - transacao_poo.quantidade_kwh
                            novo_status = 'ESGOTADO' if nova_qtd <= 0 else 'PARCIALMENTE_UTILIZADO'
                            self.db.atualizar_credito(
                                id_credito=cred_db['id_credito'],
                                quantidade_disponivel=nova_qtd,
                                novo_status=novo_status
                            )
                            break
                
                return {
                    'sucesso': True,
                    'mensagem': f"Distribuição concluída! {resultado['total_distribuido']} kWh distribuídos"
                }
            else:
                return {
                    'sucesso': False,
                    'mensagem': resultado.get('mensagem', 'Erro na distribuição')
                }
                
        except Exception as e:
            return {
                'sucesso': False,
                'mensagem': f'Erro: {str(e)}'
            }
    
    def estatisticas_gerais(self):
        """Retorna estatísticas para index.html"""
        return {
            "familias_atendidas": 850,
            "total_kwh": 1200000.0
        }
    
    def atualizar_dados_usuario(self, dados):
        """Atualiza nome e email do usuário (sem sobrenome no banco)."""
        try:
            id_usuario = int(dados.get('id_usuario', 0))
            nome = (dados.get('nome') or '').strip()
            email = (dados.get('email') or '').strip()

            if not id_usuario or not nome or not email:
                return {'sucesso': False, 'mensagem': 'Informe id_usuario, nome e email.'}

            linha = self.db.atualizar_usuario_dados(id_usuario=id_usuario, nome=nome, email=email)
            return {
                'sucesso': True,
                'mensagem': 'Dados atualizados com sucesso.',
                'usuario': linha
            }
        except Exception as e:
            # mostra erro claro no front
            return {'sucesso': False, 'mensagem': f'ERRO: {e}'}
        
    def alterar_senha(self, dados):
        """
        UPDATE credencial_usuario SET senha_hash = crypt(nova, gen_salt('bf'))
        WHERE login=$1 AND senha_hash=crypt(atual, senha_hash)
        """
        try:
            ok = self.db.atualizar_senha(dados['login'], dados['senha_atual'], dados['senha_nova'])
            return {'sucesso': ok, 'mensagem': 'Senha atualizada' if ok else 'Login/senha atual incorretos'}
        except Exception as e:
            return {'sucesso': False, 'mensagem': str(e)}

    def excluir_usuario(self, dados):
        """
        DELETE usuário + credencial, com lookup pelo email.
        """
        try:
            ok = self.db.excluir_usuario_por_email(dados['email'])
            return {'sucesso': ok, 'mensagem': 'Conta excluída' if ok else 'Usuário não encontrado'}
        except Exception as e:
            return {'sucesso': False, 'mensagem': str(e)}

    def listar_usuarios(self):
        try:
            return self.db.listar_usuarios()
        except Exception as e:
            # propaga mensagem útil para o front
            raise
