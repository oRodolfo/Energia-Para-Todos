/**
 * RECUPERAÇÃO DE SENHA - Sistema Energia para Todos
 * Fluxo em 3 etapas sem frameworks ou APIs externas
 */

let emailRecuperacao = '';
let etapaAtual = 1;

// ===== INICIALIZAÇÃO =====
document.addEventListener('DOMContentLoaded', function() {
    inicializarFormularios();
    inicializarPasswordToggle();
    inicializarValidacaoSenha();
});

// ===== NAVEGAÇÃO ENTRE ETAPAS =====
function mostrarEtapa(numero) {
    // Esconde todas as etapas
    document.querySelectorAll('.etapa').forEach(etapa => {
        etapa.classList.remove('active');
    });
    
    // Mostra etapa atual
    const etapa = document.getElementById(`etapa${numero}`);
    if (etapa) {
        etapa.classList.add('active');
        etapaAtual = numero;
        
        // Animação suave
        etapa.style.opacity = '0';
        etapa.style.transform = 'translateY(10px)';
        setTimeout(() => {
            etapa.style.opacity = '1';
            etapa.style.transform = 'translateY(0)';
        }, 50);
    }
}

// ===== FORMULÁRIOS =====
function inicializarFormularios() {
    // ETAPA 1: Solicitar código
    const formSolicitar = document.getElementById('formSolicitarCodigo');
    if (formSolicitar) {
        formSolicitar.addEventListener('submit', handleSolicitarCodigo);
    }
    
    // ETAPA 2: Validar código
    const formValidar = document.getElementById('formValidarCodigo');
    if (formValidar) {
        formValidar.addEventListener('submit', handleValidarCodigo);
    }
    
    // ETAPA 3: Nova senha
    const formNovaSenha = document.getElementById('formNovaSenha');
    if (formNovaSenha) {
        formNovaSenha.addEventListener('submit', handleNovaSenha);
    }
    
    // Botão reenviar código
    const btnReenviar = document.getElementById('btnReenviar');
    if (btnReenviar) {
        btnReenviar.addEventListener('click', function(e) {
            e.preventDefault();
            reenviarCodigo();
        });
    }
    
    // Auto-formatação do código (aceita apenas números)
    const inputCodigo = document.getElementById('codigo');
    if (inputCodigo) {
        inputCodigo.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '');
        });
    }
}

// ===== ETAPA 1: SOLICITAR CÓDIGO =====
async function handleSolicitarCodigo(e) {
    e.preventDefault();
    
    const form = e.target;
    const email = form.email.value.trim();
    
    if (!email) {
        await showModalAlert({
            title: 'Campo obrigatório',
            message: 'Por favor, informe seu email.',
            type: 'error'
        });
        return;
    }
    
    // Valida formato de email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        await showModalAlert({
            title: 'Email inválido',
            message: 'Por favor, informe um email válido.',
            type: 'error'
        });
        return;
    }
    
    try {
        const response = await fetch('http://localhost:8000/api/recuperacao/solicitar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: email })
        });
        
        const data = await response.json();
        
        if (data.sucesso) {
            // ✅ Email existe - código foi gerado
            emailRecuperacao = email;
            
            // Exibe email na etapa 2
            const emailDisplay = document.getElementById('emailEnviado');
            if (emailDisplay) {
                emailDisplay.textContent = email;
            }
            
            // Mostra código no console para facilitar testes
            if (data.codigo_debug) {
                console.log('🔑 CÓDIGO DE RECUPERAÇÃO:', data.codigo_debug);
            }
            
            // ✅ VALIDAÇÃO: Só mostra modal se código foi gerado
            if (data.codigo_debug && data.codigo_debug !== 'undefined') {
                await mostrarCodigoModal(data.codigo_debug);
                mostrarEtapa(2);
            } else {
                // Erro inesperado - código não foi gerado
                await showModalAlert({
                    title: '⚠️ Erro no sistema',
                    message: 'Não foi possível gerar o código. Tente novamente.',
                    type: 'error'
                });
            }
        } else {
            // ❌ Email não existe ou erro
            await showModalAlert({
                title: '❌ Email não encontrado',
                message: data.mensagem || 'Verifique se o email está cadastrado no sistema.',
                type: 'error'
            });
        }
        
    } catch (error) {
        console.error('Erro:', error);
        await showModalAlert({
            title: '⚠️ Erro de conexão',
            message: 'Não foi possível conectar ao servidor.',
            type: 'error'
        });
    }
}

// ===== ETAPA 2: VALIDAR CÓDIGO =====
async function handleValidarCodigo(e) {
    e.preventDefault();
    
    const form = e.target;
    const codigo = form.codigo.value.trim();
    
    if (codigo.length !== 6) {
        await showModalAlert({
            title: 'Código inválido',
            message: 'O código deve ter 6 dígitos.',
            type: 'error'
        });
        return;
    }
    
    try {
        const response = await fetch('http://localhost:8000/api/recuperacao/validar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: emailRecuperacao,
                codigo: codigo
            })
        });
        
        const data = await response.json();
        
        if (data.sucesso) {
            await showModalAlert({
                title: '✅ Código válido',
                message: 'Agora você pode criar uma nova senha.',
                type: 'success',
                onClose: () => {
                    mostrarEtapa(3);
                }
            });
        } else {
            // Tratamento detalhado: expirado vs inválido
            if (data.status === 'EXPIRADO') {
                await showModalAlert({
                    title: '⏰ Código expirado',
                    message: data.mensagem || 'Código expirado. Clique em solicitar novo código.',
                    type: 'error'
                });
                // Não avança para etapa 3 — permanece na etapa 2 até o usuário reenviar
                return;
            }

            if (data.status === 'INVALIDO') {
                await showModalAlert({
                    title: '❌ Código inválido',
                    message: data.mensagem || 'O código informado é inválido. Verifique e tente novamente.',
                    type: 'error'
                });
                return;
            }

            // Fallback genérico
            await showModalAlert({
                title: '❌ Erro',
                message: data.mensagem || 'O código está incorreto ou expirou. Solicite um novo código.',
                type: 'error'
            });
        }
        
    } catch (error) {
        console.error('Erro:', error);
        await showModalAlert({
            title: '⚠️ Erro de conexão',
            message: 'Não foi possível validar o código.',
            type: 'error'
        });
    }
}

// ===== ETAPA 3: NOVA SENHA =====
async function handleNovaSenha(e) {
    e.preventDefault();
    
    const form = e.target;
    const novaSenha = form.nova_senha.value;
    const confirmarSenha = form.confirmar_senha.value;
    
    // Validação de senha
    const validacao = validatePassword(novaSenha);
    if (!validacao.isValid) {
        await showModalAlert({
            title: 'Senha inválida',
            message: 'A senha deve ter pelo menos 8 caracteres e incluir caracteres especiais.',
            type: 'error'
        });
        return;
    }
    
    // Confirmação de senha
    if (novaSenha !== confirmarSenha) {
        await showModalAlert({
            title: 'Senhas não conferem',
            message: 'As senhas digitadas não são iguais.',
            type: 'error'
        });
        return;
    }
    
    try {
        const response = await fetch('http://localhost:8000/api/recuperacao/resetar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: emailRecuperacao,
                nova_senha: novaSenha
            })
        });
        
        const data = await response.json();
        
        if (data.sucesso) {
            await showModalAlert({
                title: '🎉 Senha alterada',
                message: 'Sua senha foi alterada com sucesso! Você será redirecionado para o login.',
                type: 'success',
                onClose: () => {
                    window.location.href = data.redirect || '/login';
                }
            });
        } else {
            await showModalAlert({
                title: '❌ Erro',
                message: data.mensagem,
                type: 'error'
            });
        }
        
    } catch (error) {
        console.error('Erro:', error);
        await showModalAlert({
            title: '⚠️ Erro de conexão',
            message: 'Não foi possível alterar a senha.',
            type: 'error'
        });
    }
}

// ===== MODAL PARA EXIBIR CÓDIGO =====
async function mostrarCodigoModal(codigo) {
    return new Promise((resolve) => {
        // Cria modal customizado
        const modal = document.createElement('div');
        modal.className = 'codigo-modal-overlay';
        modal.innerHTML = `
            <div class="codigo-modal">
                <div class="codigo-modal-header">
                    <i class="fas fa-envelope-open"></i>
                    <h3>📧 Email Recebido</h3>
                    <p>Seu código de recuperação chegou!</p>
                </div>
                <div class="codigo-modal-body">
                    <div class="codigo-email-container">
                        <div class="codigo-email-header">
                            <strong>De:</strong> noreply@energiaparatodos.com<br>
                            <strong>Para:</strong> ${emailRecuperacao}<br>
                            <strong>Assunto:</strong> Código de Recuperação de Senha
                        </div>
                        <div class="codigo-email-body">
                            <p>Olá,</p>
                            <p>Você solicitou a recuperação de senha. Use o código abaixo:</p>
                            <div class="codigo-destaque">
                                ${codigo}
                            </div>
                            <p><small>⏱️ Este código expira em 15 minutos</small></p>
                            <p><small>🔒 Se você não solicitou, ignore este email</small></p>
                        </div>
                    </div>
                </div>
                <div class="codigo-modal-footer">
                    <button class="btn btn-primary btn-neon" id="btnFecharModal">
                        <i class="fas fa-check"></i>
                        Entendi, já copiei o código
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Anima entrada
        setTimeout(() => modal.classList.add('show'), 10);
        
        // Botão fechar
        const btnFechar = modal.querySelector('#btnFecharModal');
        btnFechar.addEventListener('click', () => {
            modal.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(modal);
                resolve();
            }, 300);
        });
        
        // Auto-copia código para clipboard
        navigator.clipboard.writeText(codigo).then(() => {
            console.log('✅ Código copiado automaticamente!');
        }).catch(() => {
            console.log('⚠️ Não foi possível copiar automaticamente');
        });
    });
}

// ===== REENVIAR CÓDIGO =====
async function reenviarCodigo() {
    if (!emailRecuperacao) {
        await showModalAlert({
            title: 'Erro',
            message: 'Email não encontrado. Reinicie o processo.',
            type: 'error'
        });
        return;
    }
    
    try {
        const response = await fetch('http://localhost:8000/api/recuperacao/solicitar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: emailRecuperacao })
        });
        
        const data = await response.json();
        
        if (data.sucesso) {
            // ✅ CORREÇÃO: Sempre mostra o modal com novo código
            if (data.codigo_debug && data.codigo_debug !== 'undefined') {
                console.log('🔑 NOVO CÓDIGO:', data.codigo_debug);
                await mostrarCodigoModal(data.codigo_debug);
            } else {
                // Fallback caso não tenha código no debug
                await showModalAlert({
                    title: '✅ Código reenviado',
                    message: 'Um novo código foi gerado. Verifique o console do servidor.',
                    type: 'success'
                });
            }
        } else {
            // ❌ Erro ao reenviar
            await showModalAlert({
                title: '❌ Erro ao reenviar',
                message: data.mensagem || 'Não foi possível gerar um novo código.',
                type: 'error'
            });
        }
        
    } catch (error) {
        console.error('Erro:', error);
        await showModalAlert({
            title: '⚠️ Erro de conexão',
            message: 'Não foi possível reenviar o código.',
            type: 'error'
        });
    }
}

// ===== TOGGLE DE SENHA =====
function inicializarPasswordToggle() {
    const toggles = [
        { btn: 'toggleNovaSenha', input: 'novaSenha' },
        { btn: 'toggleConfirmar', input: 'confirmarSenha' }
    ];
    
    toggles.forEach(item => {
        const button = document.getElementById(item.btn);
        const input = document.getElementById(item.input);
        
        if (button && input) {
            button.addEventListener('click', function() {
                const type = input.type === 'password' ? 'text' : 'password';
                input.type = type;
                
                const icon = type === 'password' ? 'fa-eye' : 'fa-eye-slash';
                button.innerHTML = `<i class="fas ${icon}"></i>`;
            });
        }
    });
}

// ===== VALIDAÇÃO DE SENHA =====
function inicializarValidacaoSenha() {
    const passwordInput = document.getElementById('novaSenha');
    const strengthIndicator = document.getElementById('passwordStrength');
    
    if (passwordInput && strengthIndicator) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const strength = validatePassword(password);
            
            if (password.length === 0) {
                strengthIndicator.innerHTML = '';
                strengthIndicator.className = 'password-strength';
            } else {
                const lengthIcon = strength.minLength ? '✅' : '❌';
                const specialIcon = strength.hasSpecialChar ? '✅' : '❌';
                
                strengthIndicator.innerHTML = `
                    <div class="strength-item">${lengthIcon} 8+ caracteres</div>
                    <div class="strength-item">${specialIcon} Caracteres especiais</div>
                `;
                
                if (strength.isValid) {
                    strengthIndicator.className = 'password-strength valid';
                    this.classList.remove('invalid');
                    this.classList.add('valid');
                } else {
                    strengthIndicator.className = 'password-strength invalid';
                    this.classList.remove('valid');
                    this.classList.add('invalid');
                }
            }
        });
    }
}

function validatePassword(password) {
    const minLength = password.length >= 8;
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>_\\\/\-+=~`\[\];']/.test(password);
    
    return {
        isValid: minLength && hasSpecialChar,
        minLength,
        hasSpecialChar
    };
}

// ===== ESTILOS ADICIONAIS =====
const styles = `
    .etapa {
        display: none;
        transition: all 0.3s ease-out;
    }
    
    .etapa.active {
        display: block;
    }
    
    .etapa-header {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    .etapa-numero {
        width: 3rem;
        height: 3rem;
        background: var(--gradient-accent);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1rem;
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--color-bg-dark);
        box-shadow: var(--shadow-neon);
    }
    
    .etapa-header h3 {
        font-size: 1.25rem;
        margin-bottom: 0.5rem;
    }
    
    .etapa-header p {
        font-size: 0.875rem;
        color: var(--color-text-muted);
    }
    
    .link-voltar {
        text-align: center;
        margin-top: 1rem;
    }
    
    .link-voltar a {
        color: var(--accent);
        text-decoration: none;
        font-size: 0.875rem;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        transition: var(--transition-smooth);
    }
    
    .link-voltar a:hover {
        color: var(--accent-light);
    }
    
    #codigo {
        text-align: center;
        font-size: 1.5rem;
        letter-spacing: 0.5rem;
        font-weight: 600;
    }
    
    small {
        display: block;
        margin-top: 0.25rem;
        font-size: 0.75rem;
        color: var(--color-text-muted);
    }
    
    /* MODAL DE CÓDIGO */
    .codigo-modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(5px);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .codigo-modal-overlay.show {
        opacity: 1;
    }
    
    .codigo-modal {
        background: var(--color-bg-light);
        border: 1px solid rgba(255, 149, 0, 0.3);
        border-radius: 1rem;
        max-width: 500px;
        width: 90%;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        transform: scale(0.9);
        transition: transform 0.3s ease;
    }
    
    .codigo-modal-overlay.show .codigo-modal {
        transform: scale(1);
    }
    
    .codigo-modal-header {
        text-align: center;
        padding: 1.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .codigo-modal-header i {
        font-size: 2.5rem;
        color: var(--accent);
        margin-bottom: 0.5rem;
    }
    
    .codigo-modal-header h3 {
        font-size: 1.25rem;
        margin-bottom: 0.25rem;
    }
    
    .codigo-modal-header p {
        font-size: 0.875rem;
        color: var(--color-text-muted);
    }
    
    .codigo-modal-body {
        padding: 1.5rem;
    }
    
    .codigo-email-container {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 0.5rem;
        overflow: hidden;
    }
    
    .codigo-email-header {
        background: rgba(255, 149, 0, 0.1);
        padding: 1rem;
        font-size: 0.75rem;
        line-height: 1.6;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .codigo-email-body {
        padding: 1.5rem;
    }
    
    .codigo-email-body p {
        margin-bottom: 1rem;
        line-height: 1.6;
    }
    
    .codigo-destaque {
        background: var(--gradient-accent);
        color: var(--color-bg-dark);
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: 0.5rem;
        text-align: center;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1.5rem 0;
        box-shadow: var(--shadow-neon);
        user-select: all;
        cursor: pointer;
        transition: transform 0.2s;
    }
    
    .codigo-destaque:hover {
        transform: scale(1.05);
    }
    
    .codigo-modal-footer {
        padding: 1rem 1.5rem 1.5rem;
        text-align: center;
    }
    
    .codigo-modal-footer .btn {
        width: 100%;
    }
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = styles;
document.head.appendChild(styleSheet);