from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse, unquote
import os
import sys
import json
import uuid
from datetime import datetime, date

# Import Routes (adjusts sys.path inside file)
from routes import Routes

# Simple in-memory session store
SESSOES = {}


def criar_sessao(dados: dict) -> str:
    sid = str(uuid.uuid4())
    SESSOES[sid] = dados.copy()
    SESSOES[sid]['criada_em'] = datetime.utcnow().isoformat()
    return sid


def destruir_sessao(session_id: str):
    if session_id in SESSOES:
        del SESSOES[session_id]


def obter_session_id_from_headers(headers):
    cookie = headers.get('Cookie')
    if not cookie:
        return None
    parts = cookie.split(';')
    for p in parts:
        if '=' in p:
            k, v = p.strip().split('=', 1)
            if k == 'session_id':
                return v
    return None


class SimpleHandler(BaseHTTPRequestHandler):
    routes = Routes()

    # Utility to sync session from cookie into Routes._sessao_global
    def carregar_sessao_em_routes(self):
        sid = obter_session_id_from_headers(self.headers)
        if sid and sid in SESSOES:
            Routes._sessao_global = SESSOES[sid].copy()
            self.routes.sessao = Routes._sessao_global
        else:
            Routes._sessao_global = {}
            self.routes.sessao = Routes._sessao_global

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''

            if self.headers.get('Content-Type', '').startswith('application/json'):
                dados = json.loads(body) if body else {}
            else:
                parsed = parse_qs(body)
                dados = {k: v[0] for k, v in parsed.items()}

            path = urlparse(self.path).path

            # LOGIN
            if path in ['/login', '/api/login']:
                resultado = self.routes.login(dados)
                if resultado.get('sucesso'):
                    session_id = criar_sessao({
                        'usuario_id': Routes._sessao_global.get('usuario_id'),
                        'nome': Routes._sessao_global.get('nome'),
                        'email': Routes._sessao_global.get('email'),
                        'tipo': Routes._sessao_global.get('tipo'),
                        'id_doador': Routes._sessao_global.get('id_doador'),
                        'id_beneficiario': Routes._sessao_global.get('id_beneficiario')
                    })
                    # If redirect requested, set cookie and redirect
                    if 'redirect' in resultado:
                        self.send_response(302)
                        self.send_header('Location', resultado['redirect'])
                        self.send_header('Set-Cookie', f'session_id={session_id}; Path=/; Max-Age=86400')
                        self.end_headers()
                        return
                    return self.enviar_json(resultado)
                return self.enviar_json(resultado)

            # CADASTRO INICIAL
            if path in ['/cadastro/inicial', '/api/cadastro']:
                resultado = self.routes.cadastro_inicial(dados)
                if resultado.get('sucesso'):
                    session_id = criar_sessao({
                        'usuario_id': Routes._sessao_global.get('usuario_id'),
                        'nome': Routes._sessao_global.get('nome'),
                        'email': Routes._sessao_global.get('email'),
                        'tipo': Routes._sessao_global.get('tipo'),
                        'id_doador': Routes._sessao_global.get('id_doador'),
                        'id_beneficiario': Routes._sessao_global.get('id_beneficiario')
                    })
                    self.send_response(302)
                    self.send_header('Location', resultado.get('redirect', '/completar-cadastro'))
                    self.send_header('Set-Cookie', f'session_id={session_id}; Path=/; Max-Age=86400')
                    self.end_headers()
                    return
                return self.enviar_json(resultado)

            # PERFIL: escolha e completar
            if path == '/api/perfil/escolher':
                self.carregar_sessao_em_routes()
                if not self.routes.sessao.get('usuario_id'):
                    return self.enviar_json({
                        'sucesso': False,
                        'mensagem': 'Usuário não autenticado. Faça login novamente.',
                        'redirect': '/login'
                    }, status=401)
                
                resultado = self.routes.definir_tipo_perfil(dados.get('tipo'))
                if resultado.get('sucesso'):
                    # Atualiza sessão com o novo tipo
                    sid = obter_session_id_from_headers(self.headers)
                    if sid and sid in SESSOES:
                        SESSOES[sid].update({'tipo': Routes._sessao_global.get('tipo')})
                        # Re-envia o cookie para garantir
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json; charset=utf-8')
                        self.send_header('Set-Cookie', f'session_id={sid}; Path=/; Max-Age=86400')
                        self.end_headers()
                        json_data = json.dumps(resultado, ensure_ascii=False)
                        self.wfile.write(json_data.encode('utf-8'))
                        return
                return self.enviar_json(resultado)

            if path == '/api/perfil/completar/doador':
                self.carregar_sessao_em_routes()
                resultado = self.routes.completar_cadastro_doador(dados)
                if resultado.get('sucesso'):
                    sid = obter_session_id_from_headers(self.headers)
                    if sid and sid in SESSOES:
                        SESSOES[sid].update({
                            'id_doador': Routes._sessao_global.get('id_doador'),
                            'tipo': Routes._sessao_global.get('tipo')
                        })
                return self.enviar_json(resultado)

            if path == '/api/perfil/completar/beneficiario':
                self.carregar_sessao_em_routes()
                resultado = self.routes.completar_cadastro_beneficiario(dados)
                if resultado.get('sucesso'):
                    sid = obter_session_id_from_headers(self.headers)
                    if sid and sid in SESSOES:
                        SESSOES[sid].update({'id_beneficiario': Routes._sessao_global.get('id_beneficiario')})
                return self.enviar_json(resultado)

            # BENEFICIÁRIO - criar solicitação
            if path in ['/api/beneficiario/solicitacoes', '/api/beneficiario/solicitar']:
                self.carregar_sessao_em_routes()
                resultado = self.routes.criar_solicitacao_beneficiario(dados)
                return self.enviar_json(resultado)

            # ✅ BENEFICIÁRIO - editar solicitação
            if path == '/api/beneficiario/solicitacao/editar':
                self.carregar_sessao_em_routes()
                resultado = self.routes.editar_solicitacao(dados)
                return self.enviar_json(resultado)

            # ✅ BENEFICIÁRIO - excluir solicitação
            if path == '/api/beneficiario/solicitacao/excluir':
                self.carregar_sessao_em_routes()
                resultado = self.routes.excluir_solicitacao(dados)
                return self.enviar_json(resultado)

            # DOADOR - criar doação
            if path in ['/api/doador/doacoes', '/api/doador/doar']:
                self.carregar_sessao_em_routes()
                resultado = self.routes.criar_doacao(dados)
                # Se a criação de doação criou/definiu id_doador na sessão global,
                # persiste esse id na sessão em memória (SESSOES) para requisições futuras.
                if resultado.get('sucesso'):
                    sid = obter_session_id_from_headers(self.headers)
                    if sid and sid in SESSOES:
                        # Atualiza id_doador caso tenha sido criado agora
                        if Routes._sessao_global.get('id_doador'):
                            SESSOES[sid].update({'id_doador': Routes._sessao_global.get('id_doador')})
                return self.enviar_json(resultado)
            
            # ✅ DOADOR - editar doação
            if path == '/api/doador/doacao/editar':
                self.carregar_sessao_em_routes()
                resultado = self.routes.editar_doacao(dados)
                return self.enviar_json(resultado)

            # ✅ DOADOR - excluir doação
            if path == '/api/doador/doacao/excluir':
                self.carregar_sessao_em_routes()
                resultado = self.routes.excluir_doacao(dados)
                return self.enviar_json(resultado)
        
             # ============================================
            # ✅ CRUD DE USUÁRIOS
            # ============================================
            
            # Atualizar dados do usuário
            if path == '/usuario/atualizar-dados':
                try:
                    id_usuario = int(dados.get('id_usuario', 0))
                    nome = dados.get('nome', '').strip()
                    email = dados.get('email', '').strip()
                    
                    if not all([id_usuario, nome, email]):
                        return self.enviar_json({
                            'sucesso': False,
                            'mensagem': 'Todos os campos são obrigatórios'
                        })
                    
                    resultado = self.routes.db.atualizar_usuario_dados(id_usuario, nome, email)
                    
                    return self.enviar_json({
                        'sucesso': True,
                        'mensagem': f'Usuário #{id_usuario} atualizado com sucesso!',
                        'dados': resultado
                    })
                    
                except Exception as e:
                    print(f"❌ Erro ao atualizar usuário: {e}")
                    return self.enviar_json({
                        'sucesso': False,
                        'mensagem': f'Erro ao atualizar: {str(e)}'
                    })
            
            # Alterar senha
            if path == '/usuario/alterar-senha':
                try:
                    login = dados.get('login', '').strip()
                    senha_atual = dados.get('senha_atual', '')
                    senha_nova = dados.get('senha_nova', '')
                    
                    if not all([login, senha_atual, senha_nova]):
                        return self.enviar_json({
                            'sucesso': False,
                            'mensagem': 'Todos os campos são obrigatórios'
                        })
                    
                    sucesso = self.routes.db.atualizar_senha(login, senha_atual, senha_nova)
                    
                    if sucesso:
                        return self.enviar_json({
                            'sucesso': True,
                            'mensagem': 'Senha alterada com sucesso!'
                        })
                    else:
                        return self.enviar_json({
                            'sucesso': False,
                            'mensagem': 'Senha atual incorreta'
                        })
                        
                except Exception as e:
                    print(f"❌ Erro ao alterar senha: {e}")
                    return self.enviar_json({
                        'sucesso': False,
                        'mensagem': f'Erro ao alterar senha: {str(e)}'
                    })
            
            # Excluir usuário
            if path == '/usuario/excluir':
                try:
                    email = dados.get('email', '').strip()
                    
                    if not email:
                        return self.enviar_json({
                            'sucesso': False,
                            'mensagem': 'Email é obrigatório'
                        })
                    
                    sucesso = self.routes.db.excluir_usuario_por_email(email)
                    
                    if sucesso:
                        return self.enviar_json({
                            'sucesso': True,
                            'mensagem': f'Usuário {email} excluído com sucesso!'
                        })
                    else:
                        return self.enviar_json({
                            'sucesso': False,
                            'mensagem': 'Usuário não encontrado'
                        })
                        
                except Exception as e:
                    print(f"❌ Erro ao excluir usuário: {e}")
                    return self.enviar_json({
                        'sucesso': False,
                        'mensagem': f'Erro ao excluir: {str(e)}'
                    })

            # LOGOUT
            if path == '/api/logout':
                sid = obter_session_id_from_headers(self.headers)
                if sid:
                    destruir_sessao(sid)
                return self.enviar_json({'sucesso': True, 'redirect': '/login'})

            # Fallback
            self.enviar_404()

        except Exception as e:
            print(f"❌ Erro ao processar requisição POST: {str(e)}")
            import traceback
            traceback.print_exc()
            self.enviar_json({'sucesso': False, 'mensagem': str(e)}, status=500)

    def verificar_permissao(self, tipo_requerido):
        self.carregar_sessao_em_routes()
        if not self.routes.sessao.get('usuario_id'):
            return None
        usuario = {
            'usuario_id': self.routes.sessao.get('usuario_id'),
            'tipo_usuario': self.routes.sessao.get('tipo'),
            'email': self.routes.sessao.get('email')
        }
        if tipo_requerido is None:
            return usuario
        if tipo_requerido == 'ADMIN' and usuario['tipo_usuario'] != 'ADMINISTRADOR':
            return None
        if tipo_requerido and usuario['tipo_usuario'] not in [tipo_requerido, 'ADMINISTRADOR']:
            return None
        return usuario

    def do_GET(self):
        try:
            # Estático
            if self.path.startswith(('/assets/', '/images/')):
                return self.servir_estatico(self.path)

            if self.path == '/':
                return self.servir_html('index.html')
        
            if self.path == '/login':
                return self.servir_html('login.html')
        
            if self.path == '/cadastro':
                return self.servir_html('cadastro.html')
            
            if self.path == '/crud':
                return self.servir_html('crud.html')
            
            if self.path in ['/selecionar-perfil', '/completar-cadastro', '/painel-beneficiario', '/painel-doador']:
                self.carregar_sessao_em_routes()
                if not self.routes.sessao.get('usuario_id'):
                    # Redireciona para login se não autenticado
                    self.send_response(302)
                    self.send_header('Location', '/login')
                    self.end_headers()
                    return
            
                # Mapeia URL para arquivo HTML
                paginas = {
                    '/selecionar-perfil': 'selecionar-perfil.html',
                    '/completar-cadastro': 'completar-cadastro.html',
                    '/painel-beneficiario': 'dashboard-beneficiario.html',
                    '/painel-doador': 'dashboard-doador.html'
                }
                return self.servir_html(paginas[self.path])
        
            if self.path == '/painel-beneficiario':
                return self.servir_html('painel-beneficiario.html')
        
            if self.path == '/painel-doador':
                return self.servir_html('painel-doador.html')
        
            if self.path == '/completar-cadastro':
                return self.servir_html('completar-cadastro.html')
        
            if self.path == '/selecionar-perfil':
                return self.servir_html('selecionar-perfil.html')

            # APIs
            if self.path == '/api/meu-perfil':
                self.carregar_sessao_em_routes()
                if not self.routes.sessao.get('usuario_id'):
                    return self.enviar_json({
                        'sucesso': False,
                        'mensagem': 'Usuário não autenticado',
                        'redirect': '/login'
                    }, status=401)
            
                dados = {
                    'sucesso': True,
                    'usuario_id': self.routes.sessao.get('usuario_id'),
                    'nome': self.routes.sessao.get('nome'),
                    'email': self.routes.sessao.get('email'),
                    'tipo': self.routes.sessao.get('tipo'),
                    'id_doador': self.routes.sessao.get('id_doador'),
                    'id_beneficiario': self.routes.sessao.get('id_beneficiario')
                }
                return self.enviar_json(dados)

            # LISTAR USUÁRIOS (API)
            if self.path == '/api/usuarios':
                # Lista todos os usuários do sistema. Não exige autenticação para fins de administração local.
                try:
                    usuarios = self.routes.db.listar_usuarios(1000)
                    return self.enviar_json({'sucesso': True, 'usuarios': usuarios})
                except Exception as e:
                    print(f"❌ Erro ao listar usuários: {e}")
                    import traceback
                    traceback.print_exc()
                    return self.enviar_json({'sucesso': False, 'mensagem': str(e)}, status=500)


            if self.path == '/api/beneficiario/dados':
                self.carregar_sessao_em_routes()
                if not self.verificar_permissao('BENEFICIARIO'):
                    return self.enviar_json({'sucesso': False, 'mensagem': 'Permissão negada'}, status=403)
                dados = self.routes.obter_dados_beneficiario()
                return self.enviar_json(dados)

            if self.path == '/api/doador/dados':
                self.carregar_sessao_em_routes()
                if not self.verificar_permissao('DOADOR'):
                    return self.enviar_json({'sucesso': False, 'mensagem': 'Permissão negada'}, status=403)
                dados = self.routes.obter_dados_doador()
                return self.enviar_json(dados)

            # 404 para rotas não encontradas
            self.enviar_404()

        except Exception as e:
            print(f"❌ Erro ao processar requisição GET: {str(e)}")
            import traceback
            traceback.print_exc()
            self.enviar_json({'sucesso': False, 'mensagem': str(e)}, status=500)

    def servir_html(self, nome_arquivo, dados=None):
        cur = os.path.abspath(__file__)
        candidates = []
        base = os.path.dirname(cur)
        for _ in range(4):
            candidates.append(os.path.join(base, "FrontEnd"))
            base = os.path.dirname(base)
        FRONT_DIR = next((c for c in candidates if os.path.isdir(c)), None)
        if not FRONT_DIR:
            print("❌ Não encontrei a pasta FrontEnd. Candidatos:", candidates)
            return self.enviar_404()
        caminho = os.path.join(FRONT_DIR, nome_arquivo)
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            if dados:
                for chave, valor in dados.items():
                    conteudo = conteudo.replace(f'{{{{{chave}}}}}', str(valor))
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            
            sid = obter_session_id_from_headers(self.headers)
            if sid and sid in SESSOES:
                self.send_header('Set-Cookie', f'session_id={sid}; Path=/; Max-Age=86400; SameSite=Lax')
            
            self.end_headers()
            self.wfile.write(conteudo.encode('utf-8'))
        else:
            print(f"❌ Arquivo não encontrado: {caminho}")
            self.enviar_404()

    def servir_estatico(self, path):
        path = unquote(path)
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ASSETS_DIR = os.path.join(BASE_DIR, 'FrontEnd', 'assets')
        if path.startswith('/static/'):
            rel_path = path[len('/static/'):]
        elif path.startswith('/assets/'):
            rel_path = path[len('/assets/'):] 
        else:
            self.enviar_404(); return
        rel_path = os.path.normpath(rel_path).replace('\\', '/')
        if rel_path.startswith('..'):
            self.enviar_404(); return
        arquivo = os.path.join(ASSETS_DIR, rel_path)
        if not os.path.exists(arquivo):
            print(f"❌ Arquivo estático não encontrado: {arquivo}")
            self.enviar_404(); return
        if arquivo.endswith('.css'):
            content_type = 'text/css'
        elif arquivo.endswith('.js'):
            content_type = 'application/javascript'
        elif arquivo.endswith('.png'):
            content_type = 'image/png'
        elif arquivo.endswith('.jpg') or arquivo.endswith('.jpeg'):
            content_type = 'image/jpeg'
        elif arquivo.endswith('.svg'):
            content_type = 'image/svg+xml'
        elif arquivo.endswith('.ico'):
            content_type = 'image/x-icon'
        else:
            content_type = 'application/octet-stream'
        with open(arquivo, 'rb') as f:
            conteudo = f.read()
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()
        self.wfile.write(conteudo)

    def enviar_json(self, dados, status=200):
        import decimal
        def converter_decimal(obj):
            if isinstance(obj, decimal.Decimal):
                return float(obj)
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            raise TypeError(f'Tipo {type(obj)} não é serializável')
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        
        sid = obter_session_id_from_headers(self.headers)
        if sid and sid in SESSOES:
            self.send_header('Set-Cookie', f'session_id={sid}; Path=/; Max-Age=86400; SameSite=Lax')
        
        self.end_headers()
        json_data = json.dumps(dados, ensure_ascii=False, default=converter_decimal)
        self.wfile.write(json_data.encode('utf-8'))

    def enviar_404(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html = '''<!DOCTYPE html><html><head><title>404 - Página não encontrada</title></head><body><h1>404</h1><p>Página não encontrada</p><p><a href="/">← Voltar para o início</a></p></body></html>'''
        self.wfile.write(html.encode('utf-8'))

    def log_message(self, format, *args):
        print(f"[{self.date_time_string()}] {format % args}")


def iniciar_servidor(porta=8000):
    servidor = HTTPServer(('localhost', porta), SimpleHandler)
    print(f'\n⚡ Servidor Energia Para Todos iniciado!')
    print(f'🌐 Acesse: http://localhost:{porta}')
    print(f'🔐 Login: http://localhost:{porta}/login')
    print(f'\n💡 Pressione Ctrl+C para parar\n')
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print('\nEncerrando servidor...')
        servidor.server_close()

        print('\n\n✅ Servidor encerrado.')
        servidor.shutdown()

if __name__ == '__main__':
    iniciar_servidor()