from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json
import os
from urllib.parse import unquote
from routes import Routes

class SimpleHandler(BaseHTTPRequestHandler):
    """Handler HTTP simplificado"""
    
    routes = Routes()
    
    def do_GET(self):
        """Trata requisições GET"""
        path = urlparse(self.path).path
        
        if path == '/' or path == '/index.html':
            self.servir_html('index.html', self.routes.estatisticas_gerais())
        
        elif path == '/login' or path == '/login.html':
            self.servir_html('login.html')
        
        elif path == '/crud':              
            self.servir_html('crud.html')

        elif path == '/ods' or path == '/ods.html':
            self.servir_html('ods.html')

        elif path == '/api/usuarios':
            return self.enviar_json({'usuarios': self.routes.listar_usuarios()})
        
        elif path.startswith('/static/') or path.startswith('/assets/'):
            self.servir_estatico(path)
        
        else:
            self.enviar_404()
    
    def do_POST(self):
        """Trata requisições POST"""
        path = urlparse(self.path).path
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        dados = parse_qs(post_data)
        
        dados_limpos = {k: v[0] for k, v in dados.items()}
        print(">> POST", path, dados_limpos)  # <---- DEBUG
        
        if path == '/login':
            resultado = self.routes.login(dados_limpos)
            if resultado['sucesso']:
                self.enviar_redirect('/')
            else:
                self.enviar_html_com_mensagem('login.html', resultado['mensagem'], 'erro')
        
        elif path == '/cadastro/doador':
            resultado = self.routes.cadastro_doador(dados_limpos)
            if resultado['sucesso']:
                self.enviar_redirect('/login')
            else:
                self.enviar_html_com_mensagem('login.html', resultado['mensagem'], 'erro')
        
        # ------- CRUD extra -------
        elif path == '/usuario/atualizar-dados':
            return self.enviar_json(self.routes.atualizar_dados_usuario(dados_limpos))

        elif path == '/usuario/alterar-senha':
            return self.enviar_json(self.routes.alterar_senha(dados_limpos))

        elif path == '/usuario/excluir':
            return self.enviar_json(self.routes.excluir_usuario(dados_limpos))

        elif path == '/api/usuarios':
            # pequena “READ” p/ listar rapidamente
            return self.enviar_json({'usuarios': self.routes.listar_usuarios()})
        
        else:
            self.enviar_404()
    
    def servir_html(self, nome_arquivo, dados=None):
        """Serve arquivos HTML"""
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        FRONT_DIR = os.path.join(BASE_DIR, "FrontEnd")
        caminho = os.path.join(FRONT_DIR, nome_arquivo)

        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()

            # Substitui placeholders
            if dados:
                for chave, valor in dados.items():
                    conteudo = conteudo.replace(f'{{{{{chave}}}}}', str(valor))

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(conteudo.encode('utf-8'))
        else:
            print(f"❌ Arquivo não encontrado: {caminho}")
            self.enviar_404()
    
    def enviar_html_com_mensagem(self, arquivo, mensagem, tipo='sucesso'):
        """Serve HTML com mensagem de alerta"""
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        FRONT_DIR = os.path.join(BASE_DIR, "FrontEnd")
        caminho = os.path.join(FRONT_DIR, arquivo)
        
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            cor = '#d4edda' if tipo == 'sucesso' else '#f8d7da'
            texto_cor = '#155724' if tipo == 'sucesso' else '#721c24'
            
            alerta = f'''
            <div style="position: fixed; top: 20px; right: 20px; background: {cor}; 
                        color: {texto_cor}; padding: 1rem; border-radius: 8px; 
                        box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 9999;">
                {mensagem}
            </div>
            <script>
                setTimeout(() => {{
                    document.querySelector('div[style*="position: fixed"]').style.display = 'none';
                }}, 5000);
            </script>
            '''
            
            conteudo = conteudo.replace('</body>', f'{alerta}</body>')
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(conteudo.encode('utf-8'))
        else:
            self.enviar_404()
    
    def servir_estatico(self, path):
        import os

        # Decodifica %20, etc.
        path = unquote(path)

        # Base: .../ProjetoPIEnergia/FrontEnd/assets
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ASSETS_DIR = os.path.join(BASE_DIR, "FrontEnd", "assets")

        # Remove prefixo /static/ ou /assets/
        if path.startswith("/static/"):
            rel_path = path[len("/static/"):]
        elif path.startswith("/assets/"):
            rel_path = path[len("/assets/"):]
        else:
            self.enviar_404()
            return

        # Normaliza caminho (evita ..)
        rel_path = os.path.normpath(rel_path).replace("\\", "/")
        if rel_path.startswith(".."):
            self.enviar_404()
            return

        arquivo = os.path.join(ASSETS_DIR, rel_path)

        if not os.path.exists(arquivo):
            print(f"❌ Arquivo estático não encontrado: {arquivo}")
            self.enviar_404()
            return

        # Descobre content-type simples
        if arquivo.endswith(".css"):
            content_type = "text/css"
        elif arquivo.endswith(".js"):
            content_type = "application/javascript"
        elif arquivo.endswith(".png"):
            content_type = "image/png"
        elif arquivo.endswith(".jpg") or arquivo.endswith(".jpeg"):
            content_type = "image/jpeg"
        elif arquivo.endswith(".svg"):
            content_type = "image/svg+xml"
        elif arquivo.endswith(".ico"):
            content_type = "image/x-icon"
        else:
            content_type = "application/octet-stream"

        with open(arquivo, "rb") as f:
            conteudo = f.read()

        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(conteudo)

    def enviar_json(self, dados):
        """Envia resposta JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(dados, ensure_ascii=False).encode('utf-8'))
    
    def enviar_redirect(self, url):
        """Redireciona para outra URL"""
        self.send_response(302)
        self.send_header('Location', url)
        self.end_headers()
    
    def enviar_404(self):
        """Envia erro 404"""
        self.send_response(404)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>404 - Página não encontrada</title>
            <style>
                body { font-family: Arial; background: #0a0e27; color: white; 
                       display: flex; align-items: center; justify-content: center; 
                       height: 100vh; margin: 0; text-align: center; }
                h1 { font-size: 4rem; margin: 0; }
                p { font-size: 1.2rem; margin-top: 1rem; }
                a { color: #00d4ff; text-decoration: none; }
            </style>
        </head>
        <body>
            <div>
                <h1>404</h1>
                <p>Página não encontrada</p>
                <p><a href="/">← Voltar para o início</a></p>
            </div>
        </body>
        </html>
        '''
        self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Log das requisições"""
        print(f"[{self.date_time_string()}] {format % args}")


def iniciar_servidor(porta=8000):
    """Inicia servidor HTTP"""
    servidor = HTTPServer(('localhost', porta), SimpleHandler)
    print(f'\n⚡ Servidor Energia Para Todos iniciado!')
    print(f'🌐 Acesse: http://localhost:{porta}')
    print(f'🔐 Login: http://localhost:{porta}/login')
    print(f'\n💡 Pressione Ctrl+C para parar\n')
    
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print('\n\n✅ Servidor encerrado.')
        servidor.shutdown()


if __name__ == '__main__':
    iniciar_servidor()