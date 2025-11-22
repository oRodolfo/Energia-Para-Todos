/**
 * LIGHTPATH ACCESS - LOGIN SYSTEM
 * Sistema de login para plataforma de doação de energia solar
 * ✅ CORRIGIDO: Alertas interativos e fluxo de autenticação
 */

// ===== VARIÁVEIS GLOBAIS =====
let activeTab = 'login';
let passwordVisible = false;

// ===== INICIALIZAÇÃO =====
document.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    initializePasswordToggle();
    initializePasswordValidation();
    initializeForms();
    initializeSocialLogin();
    addAccessibilityFeatures();
});

// ===== SISTEMA DE TABS =====
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;
            switchTab(targetTab);
        });
    });
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));

    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(tabName).classList.add('active');

    activeTab = tabName;

    const activePanel = document.getElementById(tabName);
    activePanel.style.opacity = '0';
    activePanel.style.transform = 'translateY(10px)';
    
    setTimeout(() => {
        activePanel.style.opacity = '1';
        activePanel.style.transform = 'translateY(0)';
    }, 50);
}

// ===== TOGGLE DE SENHA =====
function initializePasswordToggle() {
    const toggleButton = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');

    if (toggleButton && passwordInput) {
        toggleButton.addEventListener('click', () => {
            passwordVisible = !passwordVisible;
            
            if (passwordVisible) {
                passwordInput.type = 'text';
                toggleButton.innerHTML = '<i class="fas fa-eye-slash"></i>';
            } else {
                passwordInput.type = 'password';
                toggleButton.innerHTML = '<i class="fas fa-eye"></i>';
            }
        });
    }
}

// ===== VALIDAÇÃO DE SENHA =====
function initializePasswordValidation() {
    const passwordFields = [
        { input: 'password', indicator: 'passwordStrength' },
        { input: 'registerPassword', indicator: 'registerPasswordStrength' },
    ];

    passwordFields.forEach(field => {
        const passwordInput = document.getElementById(field.input);
        let strengthIndicator = document.getElementById(field.indicator);
        
        if (passwordInput) {
            if (!strengthIndicator) {
                strengthIndicator = document.createElement('div');
                strengthIndicator.id = field.indicator;
                strengthIndicator.className = 'password-strength';
                passwordInput.parentNode.appendChild(strengthIndicator);
            }

            passwordInput.addEventListener('input', () => {
                const password = passwordInput.value;
                const strength = validatePassword(password);
                
                if (password.length === 0) {
                    strengthIndicator.innerHTML = '';
                    strengthIndicator.className = 'password-strength';
                } else {
                    const lengthIcon = strength.minLength ? '✅' : '❌';
                    const specialIcon = strength.hasSpecialChar ? '✅' : '❌';
                    
                    strengthIndicator.innerHTML = `
                        <div class="strength-item">${lengthIcon} 8+ caracteres</div>
                        <div class="strength-item">${specialIcon} Caracteres especiais (!@#$%^&*_./|\\)</div>
                    `;
                    
                    if (strength.isValid) {
                        strengthIndicator.className = 'password-strength valid';
                        passwordInput.classList.remove('invalid');
                        passwordInput.classList.add('valid');
                    } else {
                        strengthIndicator.className = 'password-strength invalid';
                        passwordInput.classList.remove('valid');
                        passwordInput.classList.add('invalid');
                    }
                }
            });
        }
    });
}

function validatePassword(password) {
    const minLength = password.length >= 8;
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>_\\\/\-+=~`\[\];']/.test(password);
    const hasNumber = /\d/.test(password);
    const hasLetter = /[a-zA-Z]/.test(password);

    return {
        isValid: minLength && hasSpecialChar,
        minLength,
        hasSpecialChar,
        hasNumber,
        hasLetter,
        score: [minLength, hasSpecialChar, hasNumber, hasLetter].filter(Boolean).length
    };
}

// ===== SISTEMA DE FORMULÁRIOS =====
function initializeForms() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegisterRegistration);
    }
}

// ✅ CORRIGIDO: Login com validação e alertas interativos
async function handleLogin(e) {
    e.preventDefault();
    const form = e.target;
    const email = form.email.value.trim();
    const password = form.password.value;
    
    // Validações
    if (!email || !password) {
        if (window.showModalAlert) {
            await window.showModalAlert({ 
                title: 'Campos obrigatórios', 
                message: 'Por favor, preencha todos os campos.', 
                type: 'error' 
            });
        }
        return;
    }
    
    const v = validatePassword(password);
    if (!v.isValid) {
        if (window.showModalAlert) {
            await window.showModalAlert({ 
                title: 'Senha inválida', 
                message: 'A senha deve ter pelo menos 8 caracteres e incluir caracteres especiais.', 
                type: 'error' 
            });
        }
        return;
    }

    try {
        // ✅ CORRIGIDO: URL correta da API
        const response = await fetch('http://localhost:8000/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (data.sucesso) {
            // ✅ Salva dados no localStorage
            localStorage.setItem('userId', data.usuario_id || '');
            localStorage.setItem('userEmail', email);
            localStorage.setItem('userToken', data.token || 'temp-token');

            // ✅ Determina redirecionamento
            let redirectUrl = '/selecionar-perfil';
            
            if (data.redirect) {
                redirectUrl = data.redirect;
            }

            // ✅ Modal interativo com redirecionamento automático
            if (window.showModalAlert) {
                await window.showModalAlert({
                    title: '✅ Login realizado',
                    message: data.mensagem || 'Bem-vindo de volta!',
                    type: 'success',
                    onClose: () => {
                        window.location.href = redirectUrl;
                    }
                });
            } else {
                window.location.href = redirectUrl;
            }
        } else {
            // ✅ Erro de credenciais - modal interativo
            if (window.showModalAlert) {
                await window.showModalAlert({
                    title: '❌ Erro de Login',
                    message: data.mensagem || 'Email ou senha incorretos. Verifique suas credenciais e tente novamente.',
                    type: 'error'
                });
            }
        }
    } catch (error) {
        console.error('Erro:', error);
        if (window.showModalAlert) {
            await window.showModalAlert({
                title: '⚠️ Erro de Conexão',
                message: 'Não foi possível conectar ao servidor. Verifique se o servidor está rodando e tente novamente.',
                type: 'error'
            });
        }
    }
}

// ✅ CORRIGIDO: Cadastro com validação e alertas interativos
async function handleRegisterRegistration(e) {
    e.preventDefault();
    const form = e.target;
    const firstName = form.firstName.value.trim();
    const lastName = form.lastName.value.trim();
    const email = form.email.value.trim();
    const password = form.password.value;
    
    // Validações
    if (!firstName || !lastName || !email || !password) {
        if (window.showModalAlert) {
            await window.showModalAlert({ 
                title: 'Campos obrigatórios',
                message: 'Por favor, preencha todos os campos.', 
                type: 'error' 
            });
        }
        return;
    }
    
    const v = validatePassword(password);
    if (!v.isValid) {
        if (window.showModalAlert) {
            await window.showModalAlert({ 
                title: 'Senha inválida', 
                message: 'A senha deve ter pelo menos 8 caracteres e incluir caracteres especiais.', 
                type: 'error' 
            });
        }
        return;
    }

    try {
        // ✅ CORRIGIDO: Envia via fetch ao invés de form.submit()
        const response = await fetch('http://localhost:8000/cadastro/inicial', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                firstName: firstName,
                lastName: lastName,
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (data.sucesso) {
            // ✅ Salva dados no localStorage
            localStorage.setItem('userId', data.usuario_id || '');
            localStorage.setItem('userEmail', email);
            localStorage.setItem('userToken', data.token || 'temp-token');

            // ✅ Modal interativo com redirecionamento
            if (window.showModalAlert) {
                await window.showModalAlert({
                    title: '🎉 Cadastro realizado',
                    message: 'Sua conta foi criada com sucesso! Agora escolha seu perfil.',
                    type: 'success',
                    onClose: () => {
                        window.location.href = data.redirect || '/selecionar-perfil';
                    }
                });
            } else {
                window.location.href = data.redirect || '/selecionar-perfil';
            }
        } else {
            // ✅ Erro no cadastro - modal interativo
            if (window.showModalAlert) {
                await window.showModalAlert({
                    title: '❌ Erro no cadastro',
                    message: data.mensagem || 'Não foi possível criar sua conta. Verifique os dados e tente novamente.',
                    type: 'error'
                });
            }
        }
    } catch (error) {
        console.error('Erro:', error);
        if (window.showModalAlert) {
            await window.showModalAlert({
                title: '⚠️ Erro de Conexão',
                message: 'Não foi possível conectar ao servidor. Verifique se o servidor está rodando e tente novamente.',
                type: 'error'
            });
        }
    }
}

// ===== LOGIN SOCIAL =====
function initializeSocialLogin() {
    const googleBtn = document.getElementById('googleLogin');
    const linkedinBtn = document.getElementById('linkedinLogin');
    const forgotPassword = document.getElementById('forgotPassword');

    if (googleBtn) {
        googleBtn.addEventListener('click', async () => {
            if (window.showModalAlert) {
                await window.showModalAlert({ 
                    title: 'Login Social', 
                    message: 'Funcionalidade em desenvolvimento. Em breve você poderá fazer login com Google.', 
                    type: 'info' 
                });
            }
        });
    }

    if (linkedinBtn) {
        linkedinBtn.addEventListener('click', async () => {
            if (window.showModalAlert) {
                await window.showModalAlert({ 
                    title: 'Login Social', 
                    message: 'Funcionalidade em desenvolvimento. Em breve você poderá fazer login com LinkedIn.', 
                    type: 'info' 
                });
            }
        });
    }

    if (forgotPassword) {
        forgotPassword.addEventListener('click', async (e) => {
            e.preventDefault();
            if (window.showModalAlert) {
                await window.showModalAlert({ 
                    title: 'Recuperação de senha', 
                    message: 'Funcionalidade em desenvolvimento. Entre em contato com o suporte.', 
                    type: 'info' 
                });
            }
        });
    }
}

// ===== ACESSIBILIDADE =====
function addAccessibilityFeatures() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach((button, index) => {
        button.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight') {
                e.preventDefault();
                const nextIndex = (index + 1) % tabButtons.length;
                tabButtons[nextIndex].focus();
                tabButtons[nextIndex].click();
            } else if (e.key === 'ArrowLeft') {
                e.preventDefault();
                const prevIndex = (index - 1 + tabButtons.length) % tabButtons.length;
                tabButtons[prevIndex].focus();
                tabButtons[prevIndex].click();
            }
        });
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const notification = document.querySelector('.notification');
            if (notification) {
                notification.querySelector('.notification-close').click();
            }
        }
    });
}

// ===== ANIMAÇÕES CSS ADICIONAIS =====
const additionalStyles = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    .password-strength {
        margin-top: 0.5rem;
        font-size: 0.75rem;
        opacity: 0.8;
    }

    .strength-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0.25rem 0;
    }

    .password-strength.valid .strength-item {
        color: #10b981;
    }

    .password-strength.invalid .strength-item {
        color: #8b949e;
    }

    input.valid {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.3) !important;
    }

    input.invalid {
        border-color: #ef4444 !important;
        box-shadow: 0 0 0 1px rgba(239, 68, 68, 0.3) !important;
    }
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);