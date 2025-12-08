document.addEventListener('DOMContentLoaded', () => {
  init();
});

function criarModalAlerta(opcoes = {}) {
  const {
    title = 'Aviso',
    message = 'Mensagem padrão',
    type = 'info',
    onClose = null,
    buttons = null
  } = opcoes;

  // Remove modal anterior se existir
  const modalAnterior = document.getElementById('cc-modal-alert');
  if (modalAnterior) {
    modalAnterior.remove();
  }

  // Cria estrutura do modal
  const modal = document.createElement('div');
  modal.id = 'cc-modal-alert';
  modal.className = 'cc-modal-overlay';

  const icones = {
    'success': '✓',
    'error': '✕',
    'warning': '⚠',
    'info': 'ℹ'
  };

  const conteudo = document.createElement('div');
  conteudo.className = `cc-modal-content cc-modal-${type}`;

  // Cabeçalho simples com ícone e título
  const header = document.createElement('div');
  header.className = 'cc-modal-header';
  header.innerHTML = `
    <span class="cc-modal-icon">${icones[type]}</span>
    <h3 class="cc-modal-title">${title}</h3>
  `;

  // Corpo com mensagem
  const body = document.createElement('div');
  body.className = 'cc-modal-body';
  body.textContent = message;

  // Rodapé com botões
  const footer = document.createElement('div');
  footer.className = 'cc-modal-footer';

  if (buttons && Array.isArray(buttons)) {
    buttons.forEach(btn => {
      const botao = document.createElement('button');
      botao.className = `cc-modal-btn ${btn.class || 'cc-modal-btn-primary'}`;
      botao.textContent = btn.label;
      botao.onclick = () => {
        if (btn.onclick) btn.onclick();
        fecharModalAlerta();
        if (onClose) onClose(btn.value);
      };
      footer.appendChild(botao);
    });
  } else {
    const btnOk = document.createElement('button');
    btnOk.className = 'cc-modal-btn cc-modal-btn-primary';
    btnOk.textContent = 'OK';
    btnOk.onclick = () => {
      fecharModalAlerta();
      if (onClose) onClose();
    };
    footer.appendChild(btnOk);
  }

  conteudo.appendChild(header);
  conteudo.appendChild(body);
  conteudo.appendChild(footer);
  modal.appendChild(conteudo);

  document.body.appendChild(modal);

  // Animação de entrada
  requestAnimationFrame(() => {
    modal.classList.add('cc-modal-show');
  });

  return modal;
}

async function init() {
  try {
    const form = document.getElementById('form-cadastro');
    const camposDiv = document.getElementById('campos-dinamicos');
    const titulo = document.getElementById('titulo-cadastro');
    const subtitulo = document.getElementById('subtitulo-cadastro');

    const meResp = await fetch('/api/meu-perfil', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (meResp.status === 401) {
      if (window.showModalAlert) {
        await window.showModalAlert({ 
          title: '❌ Sessão expirada', 
          message: 'Sua sessão expirou. Por favor, faça login novamente.', 
          type: 'error',
          onClose: () => {
            window.location.href = '/login';
          }
        });
      } else {
        window.location.href = '/login';
      }
      return;
    }
    
    if (!meResp.ok) {
      throw new Error(`Erro HTTP: ${meResp.status}`);
    }
    
    const me = await meResp.json();

    if (!me.sucesso) {
      if (window.showModalAlert) {
        await window.showModalAlert({ 
          title: '❌ Erro', 
          message: me.mensagem || 'Erro ao carregar perfil', 
          type: 'error',
          onClose: () => window.location.href = '/login'
        });
      } else {
        window.location.href = '/login';
      }
      return;
    }

    const tipo = me?.tipo;

    if (!tipo || tipo === 'null' || tipo === null || tipo === 'NOVO') {
      // Sem tipo definido - redireciona para seleção
      if (window.showModalAlert) {
        await window.showModalAlert({ 
          title: '⚠️ Perfil não definido', 
          message: 'Por favor, selecione seu perfil antes de continuar.', 
          type: 'warning',
          onClose: () => window.location.href = '/selecionar-perfil'
        });
      } else {
        window.location.href = '/selecionar-perfil';
      }
    } else if (tipo === 'DOADOR') {
      mostrarFormularioDoador(me, camposDiv, form, titulo, subtitulo);
    } else if (tipo === 'BENEFICIARIO') {
      mostrarFormularioBeneficiario(me, camposDiv, form, titulo, subtitulo);
    } else {
      if (window.showModalAlert) {
        await window.showModalAlert({ 
          title: '❌ Erro', 
          message: 'Tipo de perfil inválido.', 
          type: 'error' 
        });
      }
    }

  } catch (err) {
    console.error('Erro ao inicializar página:', err);
    if (window.showModalAlert) {
      await window.showModalAlert({ 
        title: '❌ Erro', 
        message: 'Falha ao carregar a página. Verifique sua conexão e tente novamente.', 
        type: 'error' 
      });
    }
  }
}

// ========================================
// FORMULÁRIO DO DOADOR
// ========================================
function mostrarFormularioDoador(me, camposDiv, form, titulo, subtitulo) {
  titulo.textContent = 'Completar Cadastro - Doador';
  subtitulo.textContent = 'Revise seus dados e informe a classificação:';

  camposDiv.innerHTML = `
    <div class="cc-field">
      <label for="nome">Nome</label>
      <input type="text" id="nome" name="nome" value="${me.nome || ''}" readonly>
    </div>
    <div class="cc-field">
      <label for="email">Email</label>
      <input type="email" id="email" name="email" value="${me.email || ''}" readonly>
    </div>
    <div class="cc-field">
      <label for="classificacao">Classificação</label>
      <select id="classificacao" name="classificacao" required>
        <option value="PESSOA_FISICA">Pessoa Física</option>
        <option value="PESSOA_JURIDICA">Pessoa Jurídica</option>
      </select>
    </div>

    <div id="grupo-pj" class="cc-hide">
      <div class="cc-grid">
        <div class="cc-field">
          <label for="razao_social">Razão Social</label>
          <input type="text" id="razao_social" name="razao_social" placeholder="Ex.: Energia Boa Ltda">
        </div>
        <div class="cc-field">
          <label for="cnpj">CNPJ</label>
          <input type="text" id="cnpj" name="cnpj" placeholder="00.000.000/0001-00" maxlength="18">
        </div>
      </div>
    </div>
  `;

  const classEl = document.getElementById('classificacao');
  const grupoPJ = document.getElementById('grupo-pj');
  const cnpjEl = document.getElementById('cnpj');

  const togglePJ = () => {
    if (classEl.value === 'PESSOA_JURIDICA') {
      grupoPJ.classList.remove('cc-hide');
    } else {
      grupoPJ.classList.add('cc-hide');
    }
  };

  classEl.addEventListener('change', togglePJ);
  togglePJ();

  if (cnpjEl) {
    cnpjEl.addEventListener('input', () => {
      let v = cnpjEl.value.replace(/[^\d]/g, '').slice(0, 14);
      if (v.length >= 3) v = v.replace(/^(\d{2})(\d)/, '$1.$2');
      if (v.length >= 6) v = v.replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3');
      if (v.length >= 9) v = v.replace(/^(\d{2})\.(\d{3})\.(\d{3})(\d)/, '$1.$2.$3/$4');
      if (v.length >= 13) v = v.replace(/^(\d{2})\.(\d{3})\.(\d{3})\/(\d{4})(\d)/, '$1.$2.$3/$4-$5');
      cnpjEl.value = v;
    });
  }

  form.onsubmit = async (e) => {
    e.preventDefault();

    const classificacao = classEl.value;
    let razao_social = '';
    let cnpj = '';

    if (classificacao === 'PESSOA_JURIDICA') {
      razao_social = (document.getElementById('razao_social').value || '').trim();
      cnpj = (document.getElementById('cnpj').value || '').replace(/[^\d]/g, '');
      
      if (!razao_social || !cnpj || cnpj.length !== 14) {
        if (window.showModalAlert) {
          await window.showModalAlert({ 
            title: '⚠️ Campos Obrigatórios', 
            message: 'Por favor, preencha a Razão Social e um CNPJ válido (14 dígitos).', 
            type: 'warning' 
          });
        }
        return;
      }
    }

    try {
      const resp = await fetch('/api/perfil/completar/doador', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          classificacao: classificacao,
          razao_social: classificacao === 'PESSOA_JURIDICA' ? razao_social : null,
          cnpj: classificacao === 'PESSOA_JURIDICA' ? cnpj : null
        })
      });

      const data = await resp.json();

      if (data.sucesso) {
        if (window.showModalAlert) {
          await window.showModalAlert({ 
            title: '🎉 Cadastro Concluído', 
            message: 'Seu cadastro foi completado com sucesso! Bem-vindo ao painel de doador.', 
            type: 'success',
            onClose: () => {
              window.location.href = '/painel-doador';
            }
          });
        } else {
          window.location.href = '/painel-doador';
        }
        } else {
          // Tratamento específico para duplicação de CNPJ/Razão Social
          const mensagemErro = data.mensagem || '';
          const ehDuplicacao = mensagemErro.toLowerCase().includes('unique') || 
                              mensagemErro.toLowerCase().includes('duplicat') ||
                              mensagemErro.toLowerCase().includes('já existe') ||
                              mensagemErro.toLowerCase().includes('cnpj') ||
                              mensagemErro.toLowerCase().includes('razão social');
        
          if (ehDuplicacao && classificacao === 'PESSOA_JURIDICA') {
            showModalEmpresaCadastrada();
            return;
          } else {
          if (window.showModalAlert) {
            await window.showModalAlert({ 
              title: '❌ Erro no Cadastro', 
              message: data.mensagem || 'Erro ao completar o cadastro. Por favor, tente novamente.', 
              type: 'error' 
            });
          }
        }
      }
    }catch (err) {
      console.error('Erro:', err);
      if (window.showModalAlert) {
        await window.showModalAlert({ 
          title: '⚠️ Erro de Conexão', 
          message: 'Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.', 
          type: 'error' 
        });
      }
    }
  };
}

// Adicione esta função no final do arquivo:
function showModalEmpresaCadastrada() {
  const modal = document.getElementById('modalEmpresaCadastrada');
  if (!modal) {
    const html = `
      <div class="modal-overlay" id="modalEmpresaCadastrada">
        <div class="modal-content">
          <div class="modal-header">
            <div class="modal-icon warning">
              <i class="fas fa-exclamation-circle"></i>
            </div>
            <div class="modal-header-text">
              <h2>Empresa já cadastrada</h2>
              <small>Ação necessária</small>
            </div>
          </div>
          <div class="modal-body">
            A razão social ou CNPJ informados já estão sendo utilizados no sistema. Por favor, faça login com as credenciais existentes ou cadastre outra empresa.
          </div>
          <div class="modal-footer">
            <button class="modal-btn-primary" onclick="closeModalEmpresaCadastrada()">
              <i class="fas fa-check"></i> Entendido
            </button>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', html);
  }
  document.getElementById('modalEmpresaCadastrada').classList.add('active');
}

function closeModalEmpresaCadastrada() {
  const modal = document.getElementById('modalEmpresaCadastrada');
  if (modal) modal.classList.remove('active');
}

// ========================================
// FORMULÁRIO DO BENEFICIÁRIO
// ========================================
function mostrarFormularioBeneficiario(me, camposDiv, form, titulo, subtitulo) {
  titulo.textContent = 'Completar Cadastro - Beneficiário';
  subtitulo.textContent = 'Informe suas informações de consumo e renda:';

  camposDiv.innerHTML = `
    <div class="cc-field">
      <label for="nome">Nome</label>
      <input type="text" id="nome" name="nome" value="${me.nome || ''}" readonly>
    </div>
    <div class="cc-field">
      <label for="email">Email</label>
      <input type="email" id="email" name="email" value="${me.email || ''}" readonly>
    </div>
    <div class="cc-field">
      <label for="renda_familiar">Renda Familiar Mensal (R$)</label>
      <input type="number" step="0.01" id="renda_familiar" name="renda_familiar" required>
    </div>
    <div class="cc-field">
      <label for="consumo_medio_kwh">Consumo Médio (kWh)</label>
      <input type="number" step="0.01" id="consumo_medio_kwh" name="consumo_medio_kwh" required>
    </div>
    <div class="cc-field">
      <label for="num_moradores">Número de Moradores</label>
      <input type="number" id="num_moradores" name="num_moradores" required>
    </div>
  `;

  form.onsubmit = async (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    const renda_familiar = parseFloat(formData.get('renda_familiar'));
    const consumo_medio_kwh = parseFloat(formData.get('consumo_medio_kwh'));
    const num_moradores = parseInt(formData.get('num_moradores'));

    if (isNaN(renda_familiar) || renda_familiar <= 0) {
      if (window.showModalAlert) {
        await window.showModalAlert({ 
          title: '⚠️ Campo Inválido', 
          message: 'Por favor, informe uma renda familiar válida maior que zero.', 
          type: 'warning' 
        });
      }
      return;
    }

    if (isNaN(consumo_medio_kwh) || consumo_medio_kwh <= 0) {
      if (window.showModalAlert) {
        await window.showModalAlert({ 
          title: '⚠️ Campo Inválido', 
          message: 'Por favor, informe um consumo médio válido maior que zero.', 
          type: 'warning' 
        });
      }
      return;
    }

    if (isNaN(num_moradores) || num_moradores <= 0) {
      if (window.showModalAlert) {
        await window.showModalAlert({ 
          title: '⚠️ Campo Inválido', 
          message: 'Por favor, informe um número válido de moradores maior que zero.', 
          type: 'warning' 
        });
      }
      return;
    }

    try {
      // ✅ CORREÇÃO: URL correta sem localhost
      const resp = await fetch('/api/perfil/completar/beneficiario', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          renda_familiar: renda_familiar,
          consumo_medio_kwh: consumo_medio_kwh,
          num_moradores: num_moradores
        })
      });

      const data = await resp.json();

      if (data.sucesso) {
        if (window.showModalAlert) {
          await window.showModalAlert({ 
            title: '🎉 Cadastro Concluído', 
            message: 'Seu cadastro foi completado com sucesso! Bem-vindo ao painel de beneficiário.', 
            type: 'success',
            onClose: () => {
              window.location.href = '/painel-beneficiario';
            }
          });
        } else {
          window.location.href = '/painel-beneficiario';
        }
      } else {
        if (window.showModalAlert) {
          await window.showModalAlert({ 
            title: '❌ Erro no Cadastro', 
            message: data.mensagem || 'Erro ao completar o cadastro. Por favor, tente novamente.', 
            type: 'error' 
          });
        }
      }
    } catch (err) {
      console.error('Erro:', err);
      if (window.showModalAlert) {
        await window.showModalAlert({ 
          title: '⚠️ Erro de Conexão', 
          message: 'Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.', 
          type: 'error' 
        });
      }
    }
  };
}

function getOrCreateModal(modalId, html) {
  let modal = document.getElementById(modalId);
  if (!modal) {
    document.body.insertAdjacentHTML('beforeend', html);
    modal = document.getElementById(modalId);
    
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('active');
      }
    });
  }
  return modal;
}

function closeModalInterativo(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
  }
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.active').forEach(m => {
      m.classList.remove('active');
    });
  }
});