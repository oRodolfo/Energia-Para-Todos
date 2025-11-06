/**
 * LIGHTPATH ACCESS - LOGIN SYSTEM
 * Sistema de login para plataforma de doação de energia solar
 * Funcionalidades: Tabs, validação de senha, login social
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
    // Remove active class de todos os botões e painéis
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));

    // Adiciona active class ao botão e painel selecionados
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(tabName).classList.add('active');

    activeTab = tabName;

    // Animação suave
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
    // Array com todos os IDs de campos de senha
    const passwordFields = [
        { input: 'password', indicator: 'passwordStrength' },
        { input: 'registerPassword', indicator: 'registerPasswordStrength' },
    ];

    passwordFields.forEach(field => {
        const passwordInput = document.getElementById(field.input);
        let strengthIndicator = document.getElementById(field.indicator);
        
        if (passwordInput) {
            // Se não existe o indicador, cria um
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
    // Inclui todos os caracteres especiais que você mencionou
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

// ===== FORMATAÇÃO DE CAMPOS =====
function formatCNPJ(value) {
    value = value.replace(/\D/g, '');
    value = value.replace(/^(\d{2})(\d)/, '$1.$2');
    value = value.replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3');
    value = value.replace(/\.(\d{3})(\d)/, '.$1/$2');
    value = value.replace(/(\d{4})(\d)/, '$1-$2');
    return value;
}

// ===== SISTEMA DE FORMULÁRIOS =====
function initializeForms() {
    // Formulário de Login
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Formulário de Cadastro
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleregisterRegistration);
    }

}

function handleLogin(e) {
    const form = e.target;
    const email = form.email.value.trim();
    const password = form.password.value;
    
    // Validações
    if (!email || !password) {
        e.target.submit();
        showNotification('Por favor, preencha todos os campos.', 'error');
        return;
    }
    
    const v = validatePassword(password);
    if (!v.isValid) {
        e.target.submit();
        showNotification('Senha deve ter pelo menos 8 caracteres e símbolos.', 'error');
        return;
    }

    form.action = '/login';
    form.method = 'POST';
}

function handleregisterRegistration(e) {
    e.preventDefault();
    const form = e.target;
    const firstName = form.firstName.value.trim();
    const lastName  = form.lastName.value.trim();
    const email     = form.email.value.trim();
    const password  = form.password.value;
    
    // Validações
    if (!firstName || !lastName || !email || !password) {
        e.target.submit();
        showNotification('Por favor, preencha todos os campos.', 'error');
        return;
    }
    
    // Validação da senha
    const v = validatePassword(password);
    if (!v.isValid) {
        e.target.submit();
        showNotification('A senha deve ter pelo menos 8 caracteres e incluir símbolos.', 'error');
        return;
    }

    form.submit();
}

function handleReceiverRegistration(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const firstName = formData.get('firstName');
    const lastName = formData.get('lastName');
    const email = formData.get('email');
    const password = formData.get('password');
    
    // Validações
    if (!firstName || !lastName || !email || !password) {
        showNotification('Por favor, preencha todos os campos.', 'error');
        return;
    }
    
    // Validação da senha
    const passwordValidation = validatePassword(password);
    if (!passwordValidation.isValid) {
        showNotification('A senha deve ter pelo menos 8 caracteres e incluir símbolos especiais.', 'error');
        return;
    }
    
    // Simula cadastro
    showNotification('Criando conta de recebedor...', 'info');
    setTimeout(() => {
        showNotification('Conta criada com sucesso! Em breve você receberá informações sobre doações disponíveis.', 'success');
    }, 1500);
}

function handleCompanyRegistration(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const companyName = formData.get('companyName');
    const cnpj = formData.get('cnpj');
    const email = formData.get('email');
    const password = formData.get('password');
    
    // Validações
    if (!companyName || !cnpj || !email || !password) {
        showNotification('Por favor, preencha todos os campos.', 'error');
        return;
    }
    
    if (!validateCNPJ(cnpj)) {
        showNotification('CNPJ inválido. Verifique os dados informados.', 'error');
        return;
    }
    
    // Validação da senha - ADICIONE ESTA PARTE
    const passwordValidation = validatePassword(password);
    if (!passwordValidation.isValid) {
        showNotification('A senha deve ter pelo menos 8 caracteres e incluir símbolos especiais.', 'error');
        return;
    }
    
    // Simula cadastro
    showNotification('Enviando dados para análise...', 'info');
    setTimeout(() => {
        showNotification('Cadastro enviado! Você receberá um email com o resultado da análise.', 'success');
    }, 2000);
}

// ===== LOGIN SOCIAL =====
function initializeSocialLogin() {
    const googleBtn = document.getElementById('googleLogin');
    const linkedinBtn = document.getElementById('linkedinLogin');
    const forgotPassword = document.getElementById('forgotPassword');

    if (googleBtn) {
        googleBtn.addEventListener('click', () => {
            showNotification('Redirecionando para Google...', 'info');
            // Aqui você integraria com a API do Google
        });
    }

    if (linkedinBtn) {
        linkedinBtn.addEventListener('click', () => {
            showNotification('Redirecionando para LinkedIn...', 'info');
            // Aqui você integraria com a API do LinkedIn
        });
    }

    if (forgotPassword) {
        forgotPassword.addEventListener('click', (e) => {
            e.preventDefault();
            showNotification('Funcionalidade de recuperação de senha em desenvolvimento.', 'info');
        });
    }
}

// ===== SISTEMA DE NOTIFICAÇÕES =====
function showNotification(message, type = 'info') {
    // Remove notificação existente
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    // Cria nova notificação
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getIconForType(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close">
            <i class="fas fa-times"></i>
        </button>
    `;

    // Estilos da notificação
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${getBackgroundForType(type)};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        max-width: 300px;
        animation: slideInRight 0.3s ease-out;
    `;

    document.body.appendChild(notification);

    // Fecha notificação
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    });

    // Auto-close
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

function getIconForType(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        info: 'info-circle',
        warning: 'exclamation-triangle'
    };
    return icons[type] || 'info-circle';
}

function getBackgroundForType(type) {
    const backgrounds = {
        success: 'linear-gradient(135deg, #10b981, #059669)',
        error: 'linear-gradient(135deg, #ef4444, #dc2626)',
        info: 'linear-gradient(135deg, #3b82f6, #2563eb)',
        warning: 'linear-gradient(135deg, #f59e0b, #d97706)'
    };
    return backgrounds[type] || backgrounds.info;
}

// ===== ACESSIBILIDADE =====
function addAccessibilityFeatures() {
    // Navegação por teclado nas tabs
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

    // Escape para fechar notificações
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const notification = document.querySelector('.notification');
            if (notification) {
                notification.querySelector('.notification-close').click();
            }
        }
    });
}

function handleReceiverRegistration(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const firstName = formData.get('firstName');
    const lastName = formData.get('lastName');
    const email = formData.get('email');
    const password = formData.get('password');
    
    // Validações
    if (!firstName || !lastName || !email || !password) {
        showNotification('Por favor, preencha todos os campos.', 'error');
        return;
    }
    
    // Simula cadastro
    showNotification('Criando conta de recebedor...', 'info');
    setTimeout(() => {
        showNotification('Conta criada com sucesso! Em breve você receberá informações sobre doações disponíveis.', 'success');
    }, 1500);
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

    .notification-content {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .notification-close {
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        padding: 0.25rem;
        border-radius: 0.25rem;
        transition: background-color 0.2s;
    }

    .notification-close:hover {
        background: rgba(255, 255, 255, 0.2);
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

// Adiciona estilos adicionais
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);
