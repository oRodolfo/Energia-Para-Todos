# --- Caminho para o BackEnd ---
import os, sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "BackEnd")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from datetime import datetime, timedelta

from database import Database

class Routes:
    """
    Classe responsável por gerenciar as rotas da aplicação.
    
    FUNCIONALIDADES:
    - Login de usuários
    - Cadastro de doadores
    - CRUD completo de usuários (Atualizar, Alterar senha, Excluir, Listar)
    - Estatísticas gerais (parcial - apenas para index.html)
    """
    
    def __init__(self):
        self.db = Database()
        self.sessao = {}
    
    def login(self, dados):
        """
        Processa login de usuários validando email e senha.
        """
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
        """
        Cadastra novo doador com firstName, lastName, email e password.
        """
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
    
    def atualizar_dados_usuario(self, dados):
        """
        Atualiza nome e email do usuário.
        """
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
            return {'sucesso': False, 'mensagem': f'ERRO: {e}'}
        
    def alterar_senha(self, dados):
        """
        Altera senha do usuário validando a senha atual.
        """
        try:
            ok = self.db.atualizar_senha(dados['login'], dados['senha_atual'], dados['senha_nova'])
            return {'sucesso': ok, 'mensagem': 'Senha atualizada' if ok else 'Login/senha atual incorretos'}
        except Exception as e:
            return {'sucesso': False, 'mensagem': str(e)}

    def excluir_usuario(self, dados):
        """
        Exclui usuário e todas suas dependências pelo email.
        """
        try:
            ok = self.db.excluir_usuario_por_email(dados['email'])
            return {'sucesso': ok, 'mensagem': 'Conta excluída' if ok else 'Usuário não encontrado'}
        except Exception as e:
            return {'sucesso': False, 'mensagem': str(e)}

    def listar_usuarios(self):
        """
        Lista todos os usuários cadastrados.
        """
        try:
            return self.db.listar_usuarios()
        except Exception as e:
            raise
    
    def estatisticas_gerais(self):
        """
        Retorna estatísticas estáticas para index.html.
        """
        return {
            "familias_atendidas": 850,
            "total_kwh": 1200000.0
        }