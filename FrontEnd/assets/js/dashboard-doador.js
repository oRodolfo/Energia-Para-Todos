// DASHBOARD DOADOR - VERSÃO ATUALIZADA
let dadosDoador = null;

// INICIALIZAÇÃO
document.addEventListener('DOMContentLoaded', async () => {
  console.log('🚀 Dashboard Doador iniciado');
  await carregarDadosDoador();
  configurarEventos();
  configurarModalEdicao();
  configurarNavegacao();
});

// CARREGAR DADOS DO DOADOR
async function carregarDadosDoador() {
  try {
    const response = await fetch('/api/doador/dados', {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    const resultado = await response.json();
    if (!resultado.sucesso) {
      mostrarAlerta(resultado.mensagem || 'Erro ao carregar dados', 'error');
      if (resultado.mensagem && resultado.mensagem.includes('Permissão negada')) {
        setTimeout(() => window.location.href = '/login', 2000);
      }
      return;
    }
    const dados = resultado.dados;
    
    let nomeExibicao = dados.nome;
    if (dados.classificacao === 'PESSOA_JURIDICA' && dados.razao_social) {
      nomeExibicao = dados.razao_social;
    }
    
    document.querySelector('.dashboard-title').textContent = `Olá, ${nomeExibicao}`;

    const subtitulo = document.querySelector('.dashboard-subtitle');
    if (dados.cnpj) {
      subtitulo.textContent = `Pessoa Jurídica · CNPJ: ${formatarCNPJ(dados.cnpj)}`;
    } else {
      subtitulo.textContent = 'Pessoa Física';
    }

    dadosDoador = dados;
    renderizarDashboard(dados);
    
  } catch (erro) {
    console.error('❌ Erro ao carregar dados:', erro);
    mostrarAlerta('Erro ao conectar com o servidor', 'error');
  }
}

function formatarCNPJ(cnpj) {
  if (!cnpj) return '';
  return cnpj.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
}

// RENDERIZAR DASHBOARD
function renderizarDashboard(dados) {
  console.log('📊 Renderizando dashboard:', dados);

  document.getElementById('total-doado').innerHTML = 
    `${dados.total_doado_kwh || 0} <span>kWh</span>`;
  
  document.getElementById('total-distribuido').innerHTML = 
    `${dados.total_distribuido_kwh || 0} <span>kWh</span>`;
  
  document.getElementById('familias-atendidas').textContent = 
    dados.familias_atendidas || 0;
  
  document.getElementById('co2-reduzido').innerHTML = 
    `${dados.co2_reduzido_kg || 0} <span>kg</span>`;

  renderizarHistorico(dados.creditos || []);
}

// RENDERIZAR HISTÓRICO COM FILTROS
function renderizarHistoricoComFiltros(creditos) {
  creditosOriginais = creditos || [];
  
  const container = document.getElementById('historico-doacoes');
  
  if (!creditos || creditos.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-inbox"></i>
        <p>Nenhuma doação registrada ainda</p>
        <p class="empty-state-hint">Clique em "Registrar Nova Doação" para começar</p>
      </div>
    `;
    return;
  }

  let creditosFiltrados = aplicarFiltros(creditos);

  let html = `
    <div class="filtros-container">
      <div class="filtros-header">
        <span class="filtros-titulo">
          <i class="fas fa-filter"></i> Filtros
        </span>
        <button class="btn-limpar-filtros" onclick="limparFiltros()" title="Limpar todos os filtros">
          <i class="fas fa-times"></i> Limpar
        </button>
      </div>
      
      <div class="filtros-grid">
        <div class="filtro-item">
          <label class="filtro-label">
            <i class="fas fa-circle-check"></i> Status
          </label>
          <select class="filtro-select" id="filtro-status" onchange="atualizarFiltroStatus(this.value)">
            <option value="TODOS">Todos os Status</option>
            <option value="DISPONIVEL">✅ Disponível</option>
            <option value="PARCIALMENTE_UTILIZADO">⚠️ Parcialmente Utilizado</option>
            <option value="ESGOTADO">❌ Esgotado</option>
            <option value="EXPIRADO">⏰ Expirado</option>
          </select>
        </div>

        <div class="filtro-item">
          <label class="filtro-label">
            <i class="fas fa-calendar"></i> Data de Expiração
          </label>
          <div class="filtro-data-group">
            <input type="date" class="filtro-input" id="filtro-data-inicio" 
                   onchange="atualizarFiltroData()" placeholder="De">
            <span class="filtro-separador">até</span>
            <input type="date" class="filtro-input" id="filtro-data-fim" 
                   onchange="atualizarFiltroData()" placeholder="Até">
          </div>
        </div>

        <div class="filtro-item">
          <label class="filtro-label">
            <i class="fas fa-bolt"></i> Quantidade Inicial (kWh)
          </label>
          <div class="filtro-data-group">
            <input type="number" class="filtro-input" id="filtro-qtd-min" 
                   onchange="atualizarFiltroQuantidade()" placeholder="Mínimo" step="0.01">
            <span class="filtro-separador">até</span>
            <input type="number" class="filtro-input" id="filtro-qtd-max" 
                   onchange="atualizarFiltroQuantidade()" placeholder="Máximo" step="0.01">
          </div>
        </div>
      </div>

      <div class="filtros-info">
        <span class="filtros-resultado">
          <i class="fas fa-list"></i> 
          Mostrando <strong>${creditosFiltrados.length}</strong> de <strong>${creditos.length}</strong> doações
        </span>
      </div>
    </div>
  `;

  if (creditosFiltrados.length === 0) {
    html += `
      <div class="empty-state">
        <i class="fas fa-search"></i>
        <p>Nenhuma doação encontrada com os filtros aplicados</p>
        <p class="empty-state-hint">Tente ajustar os filtros ou clique em "Limpar"</p>
      </div>
    `;
    container.innerHTML = html;
    return;
  }

  html += `
    <table class="table-crud">
      <thead>
        <tr>
          <th><i class="fas fa-bolt"></i> CRÉDITO</th>
          <th>QUANTIDADE INICIAL</th>
          <th>DISPONÍVEL</th>
          <th>DISTRIBUÍDO</th>
          <th>STATUS</th>
          <th>EXPIRA EM</th>
          <th class="th-acoes">AÇÕES</th>
        </tr>
      </thead>
      <tbody>
  `;

  creditosFiltrados.forEach(credito => {
    const qtdInicial = parseFloat(credito.quantidade_inicial || 0);
    const qtdDisponivel = parseFloat(credito.quantidade_disponivel_kwh || 0);
    const qtdConsumida = parseFloat(credito.quantidade_consumida || 0);
    
    // ✅ CALCULA STATUS REAL BASEADO NOS DADOS
    let statusReal = '';
    let statusClass = '';
    let statusIcon = '';
    
    if (qtdConsumida === 0) {
      // 🟢 DISPONÍVEL - Nada foi consumido ainda
      statusReal = 'DISPONÍVEL';
      statusClass = 'status-success';
      statusIcon = '🟢';
    } else if (qtdConsumida > 0 && qtdDisponivel > 0) {
      // 🟠 PARCIALMENTE UTILIZADO - Foi consumido algo, mas ainda sobra
      statusReal = 'PARCIALMENTE UTILIZADO';
      statusClass = 'status-warning';
      statusIcon = '🟠';
    } else if (qtdDisponivel === 0) {
      // 🔴 ESGOTADO - Nada mais disponível
      statusReal = 'ESGOTADO';
      statusClass = 'status-danger';
      statusIcon = '🔴';
    }
    
    const dataExpiracao = credito.data_expiracao 
      ? new Date(credito.data_expiracao).toLocaleDateString('pt-BR')
      : 'Sem data';

    // ✅ Doação pode ser editada/excluída apenas se NÃO foi consumida
    const podeEditar = qtdConsumida === 0;

    html += `
      <tr>
        <td><span class="badge badge-primary">⚡ #${credito.id_credito}</span></td>
        <td><strong>${qtdInicial.toFixed(2)} kWh</strong></td>
        <td><span style="color: #22c55e; font-weight: 700;">${qtdDisponivel.toFixed(2)} kWh</span></td>
        <td><span style="color: #ef4444; font-weight: 700;">${qtdConsumida.toFixed(2)} kWh</span></td>
        <td><span class="badge ${statusClass}">${statusIcon} ${statusReal}</span></td>
        <td>📅 ${dataExpiracao}</td>
        <td class="td-acoes">
    `;

    if (podeEditar) {
      html += `
        <button class="btn-action btn-edit" onclick="abrirModalEdicao(${credito.id_credito}, ${qtdInicial})" title="Editar doação">
          <i class="fas fa-edit"></i>
        </button>
        <button class="btn-action btn-delete" onclick="confirmarExclusao(${credito.id_credito})" title="Excluir doação">
          <i class="fas fa-trash"></i>
        </button>
      `;
    } else {
      html += `
        <span class="badge badge-info" title="Esta doação já foi distribuída (${qtdConsumida.toFixed(2)} kWh consumidos)">
          <i class="fas fa-lock"></i> Distribuída
        </span>
      `;
    }

    html += `
        </td>
      </tr>
    `;
  });

  html += '</tbody></table>';
  container.innerHTML = html;

  restaurarValoresFiltros();
}

// Variável para armazenar filtros ativos
let filtrosAtivos = {
  status: 'TODOS',
  dataInicio: null,
  dataFim: null,
  quantidadeMin: null,
  quantidadeMax: null
};

let creditosOriginais = [];

function aplicarFiltros(creditos) {
  return creditos.filter(credito => {
    // Calcula status real para filtrar
    const qtdConsumida = parseFloat(credito.quantidade_consumida || 0);
    const qtdDisponivel = parseFloat(credito.quantidade_disponivel_kwh || 0);
    
    let statusReal = '';
    if (qtdConsumida === 0) {
      statusReal = 'DISPONIVEL';
    } else if (qtdConsumida > 0 && qtdDisponivel > 0) {
      statusReal = 'PARCIALMENTE_UTILIZADO';
    } else if (qtdDisponivel === 0) {
      statusReal = 'ESGOTADO';
    }
    
    if (filtrosAtivos.status !== 'TODOS') {
      if (statusReal !== filtrosAtivos.status) {
        return false;
      }
    }

    if (filtrosAtivos.dataInicio || filtrosAtivos.dataFim) {
      const dataExpiracao = credito.data_expiracao ? new Date(credito.data_expiracao) : null;
      
      if (dataExpiracao) {
        if (filtrosAtivos.dataInicio) {
          const dataInicio = new Date(filtrosAtivos.dataInicio);
          if (dataExpiracao < dataInicio) return false;
        }
        
        if (filtrosAtivos.dataFim) {
          const dataFim = new Date(filtrosAtivos.dataFim);
          if (dataExpiracao > dataFim) return false;
        }
      }
    }

    const qtdInicial = parseFloat(credito.quantidade_inicial || 0);
    
    if (filtrosAtivos.quantidadeMin !== null) {
      if (qtdInicial < filtrosAtivos.quantidadeMin) return false;
    }
    
    if (filtrosAtivos.quantidadeMax !== null) {
      if (qtdInicial > filtrosAtivos.quantidadeMax) return false;
    }

    return true;
  });
}

function atualizarFiltroStatus(status) {
  filtrosAtivos.status = status;
  renderizarHistoricoComFiltros(creditosOriginais);
  mostrarAlerta(`Filtro aplicado: ${status === 'TODOS' ? 'Todos os status' : status}`, 'info');
}

function atualizarFiltroData() {
  const dataInicio = document.getElementById('filtro-data-inicio').value;
  const dataFim = document.getElementById('filtro-data-fim').value;
  
  filtrosAtivos.dataInicio = dataInicio || null;
  filtrosAtivos.dataFim = dataFim || null;
  
  renderizarHistoricoComFiltros(creditosOriginais);
  
  if (dataInicio || dataFim) {
    mostrarAlerta('Filtro de data aplicado', 'info');
  }
}

function atualizarFiltroQuantidade() {
  const qtdMin = document.getElementById('filtro-qtd-min').value;
  const qtdMax = document.getElementById('filtro-qtd-max').value;
  
  filtrosAtivos.quantidadeMin = qtdMin ? parseFloat(qtdMin) : null;
  filtrosAtivos.quantidadeMax = qtdMax ? parseFloat(qtdMax) : null;
  
  renderizarHistoricoComFiltros(creditosOriginais);
  
  if (qtdMin || qtdMax) {
    mostrarAlerta('Filtro de quantidade aplicado', 'info');
  }
}

function limparFiltros() {
  filtrosAtivos = {
    status: 'TODOS',
    dataInicio: null,
    dataFim: null,
    quantidadeMin: null,
    quantidadeMax: null
  };
  
  document.getElementById('filtro-status').value = 'TODOS';
  document.getElementById('filtro-data-inicio').value = '';
  document.getElementById('filtro-data-fim').value = '';
  document.getElementById('filtro-qtd-min').value = '';
  document.getElementById('filtro-qtd-max').value = '';
  
  renderizarHistoricoComFiltros(creditosOriginais);
  mostrarAlerta('Filtros limpos! Mostrando todas as doações', 'success');
}

function restaurarValoresFiltros() {
  const selectStatus = document.getElementById('filtro-status');
  const inputDataInicio = document.getElementById('filtro-data-inicio');
  const inputDataFim = document.getElementById('filtro-data-fim');
  const inputQtdMin = document.getElementById('filtro-qtd-min');
  const inputQtdMax = document.getElementById('filtro-qtd-max');

  if (selectStatus) selectStatus.value = filtrosAtivos.status;
  if (inputDataInicio) inputDataInicio.value = filtrosAtivos.dataInicio || '';
  if (inputDataFim) inputDataFim.value = filtrosAtivos.dataFim || '';
  if (inputQtdMin) inputQtdMin.value = filtrosAtivos.quantidadeMin || '';
  if (inputQtdMax) inputQtdMax.value = filtrosAtivos.quantidadeMax || '';
}

function renderizarHistorico(creditos) {
  renderizarHistoricoComFiltros(creditos);
}

function configurarEventos() {
  const btnAbrirModal = document.getElementById('btn-abrir-modal');
  const btnFecharModal = document.getElementById('btn-fechar-modal');
  const btnConfirmar = document.getElementById('btn-confirmar-doacao');
  const modalOverlay = document.getElementById('modal-doacao');

  btnAbrirModal?.addEventListener('click', () => {
    modalOverlay.style.display = 'flex';
    document.getElementById('input-kwh').value = '';
  });

  btnFecharModal?.addEventListener('click', () => {
    modalOverlay.style.display = 'none';
  });

  btnConfirmar?.addEventListener('click', criarDoacao);

  modalOverlay?.addEventListener('click', (e) => {
    if (e.target === modalOverlay) {
      modalOverlay.style.display = 'none';
    }
  });

  configurarNavegacao();
}

function configurarNavegacao() {
  const btnInicio = document.getElementById('btn-inicio');
  const btnEditar = document.getElementById('btn-editar');
  const btnLogout = document.getElementById('btn-logout');

  btnInicio?.addEventListener('click', () => {
    window.location.href = '/';
  });

  btnEditar?.addEventListener('click', () => {
    const modal = document.getElementById('modal-editar-perfil');
    if (modal) {
      carregarDadosParaEdicao();
      modal.classList.add('show');
    } else {
      window.location.href = '/editar-perfil-doador';
    }
  });

  btnLogout?.addEventListener('click', async () => {
    if (confirm('Deseja realmente sair do sistema?')) {
      try {
        await fetch('/api/logout', {
          method: 'POST',
          credentials: 'include'
        });
        
        mostrarAlerta('Logout realizado com sucesso!', 'success');
        
        setTimeout(() => {
          window.location.href = '/login';
        }, 1000);
        
      } catch (erro) {
        console.error('Erro ao fazer logout:', erro);
        window.location.href = '/login';
      }
    }
  });
}

function configurarModalEdicao() {
  const modal = document.getElementById('modal-editar-perfil');
  const btnFechar = document.getElementById('btn-fechar-modal-editar');
  const btnSalvar = document.getElementById('btn-salvar-perfil');
  const form = document.getElementById('form-editar-perfil');

  if (form && !document.getElementById('alterar-senha-toggle')) {
    const container = document.createElement('div');
    container.className = 'form-group';
    container.innerHTML = `
      <label class="modal-label">Alterar senha (opcional)</label>
      <div style="display:flex;gap:8px;align-items:center;">
        <input type="checkbox" id="alterar-senha-toggle" />
        <small style="color:#ffd34d">Marque para alterar sua senha</small>
      </div>
      <div id="senha-fields" style="margin-top:10px;display:none">
        <input type="password" id="senha-atual" class="modal-input" placeholder="Senha atual">
        <input type="password" id="senha-nova" class="modal-input" placeholder="Nova senha (mínimo 6 caracteres)" style="margin-top:8px">
      </div>
    `;
    form.appendChild(container);

    document.getElementById('alterar-senha-toggle').addEventListener('change', (e) => {
      const show = e.target.checked;
      document.getElementById('senha-fields').style.display = show ? 'block' : 'none';
    });
  }

  btnFechar?.addEventListener('click', () => {
    modal.classList.remove('show');
  });

  form?.addEventListener('submit', (ev) => {
    ev.preventDefault();
    salvarEdicaoPerfil();
  });

  btnSalvar?.addEventListener('click', (ev) => {
    ev.preventDefault();
    salvarEdicaoPerfil();
  });

  modal?.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.classList.remove('show');
    }
  });
}

async function carregarDadosParaEdicao() {
  try {
    const resp = await fetch('/api/meu-perfil', { credentials: 'include' });
    const data = await resp.json();

    if (data.sucesso && data.dados) {
      document.getElementById('input-nome').value = data.dados.nome || '';
      document.getElementById('input-email').value = data.dados.email || '';
    } else {
      mostrarAlerta(data.mensagem || 'Erro ao carregar dados', 'error');
    }
  } catch (err) {
    console.error('Erro ao carregar dados para edição:', err);
    mostrarAlerta('Erro ao carregar seus dados', 'error');
  }
}

async function salvarEdicaoPerfil() {
  try {
    const nome = document.getElementById('input-nome').value.trim();
    const email = document.getElementById('input-email').value.trim();
    const alterarSenha = document.getElementById('alterar-senha-toggle')?.checked;
    const senhaAtual = document.getElementById('senha-atual')?.value || '';
    const senhaNova = document.getElementById('senha-nova')?.value || '';

    if (!nome || !email) {
      mostrarAlerta('Preencha nome e email corretamente.', 'warning');
      return;
    }

    if (!email.includes('@')) {
      mostrarAlerta('Email inválido', 'warning');
      return;
    }

    // VALIDAÇÃO DE SENHA ANTES DE TUDO
    if (alterarSenha) {
      if (!senhaAtual || !senhaNova) {
        mostrarAlerta('Preencha a senha atual e a nova senha.', 'warning');
        return;
      }
      if (senhaNova.length < 8) {
        mostrarAlerta('A nova senha deve ter no mínimo 8 caracteres.', 'warning');
        return;
      }
    }

    // 1. ATUALIZA NOME E EMAIL
    const respDados = await fetch('/usuario/atualizar-dados', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `nome=${encodeURIComponent(nome)}&email=${encodeURIComponent(email)}`
    });

    const resultDados = await respDados.json();
    if (!resultDados.sucesso) {
      mostrarAlerta(resultDados.mensagem || 'Erro ao atualizar dados', 'error');
      return;
    }

    // 2. ATUALIZA SENHA (SE SOLICITADO)
    if (alterarSenha) {
      const respSenha = await fetch('/usuario/alterar-senha', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `login=${encodeURIComponent(email)}&senha_atual=${encodeURIComponent(senhaAtual)}&senha_nova=${encodeURIComponent(senhaNova)}`
      });

      const resultSenha = await respSenha.json();
      if (!resultSenha.sucesso) {
        mostrarAlerta(resultSenha.mensagem || 'Erro ao alterar senha', 'error');
        return;
      }
    }

    // 3. SUCESSO
    mostrarAlerta('✔ Perfil atualizado com sucesso!', 'success');
    document.getElementById('modal-editar-perfil').classList.remove('show');
    
    // Limpa campos de senha
    if (document.getElementById('alterar-senha-toggle')) {
      document.getElementById('alterar-senha-toggle').checked = false;
      document.getElementById('senha-fields').style.display = 'none';
      document.getElementById('senha-atual').value = '';
      document.getElementById('senha-nova').value = '';
    }
    
    // Recarrega dados
    setTimeout(() => carregarDadosDoador(), 800);

  } catch (err) {
    console.error('Erro ao salvar perfil:', err);
    mostrarAlerta('Erro ao salvar as alterações', 'error');
  }
}

async function realizarLogout() {
  try {
    await fetch('/api/logout', { method: 'POST', credentials: 'include' });
    localStorage.clear();
    sessionStorage.clear();
    mostrarAlerta('Você foi desconectado com sucesso!', 'success');
    setTimeout(() => { window.location.href = '/login'; }, 800);
  } catch (err) {
    console.error('Erro ao fazer logout:', err);
    window.location.href = '/login';
  }
}

async function criarDoacao() {
  const inputKwh = document.getElementById('input-kwh');
  const quantidade = parseFloat(inputKwh.value);

  if (!quantidade || quantidade <= 0) {
    mostrarAlerta('Por favor, insira uma quantidade válida', 'warning');
    return;
  }

  try {
    const response = await fetch('/api/doador/doar', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantidade_kwh: quantidade })
    });

    const resultado = await response.json();

    if (resultado.sucesso) {
      mostrarAlerta(`Doação de ${quantidade} kWh registrada com sucesso! 🎉`, 'success');
      document.getElementById('modal-doacao').style.display = 'none';
      await carregarDadosDoador();
    } else {
      mostrarAlerta(resultado.mensagem || 'Erro ao registrar doação', 'error');
    }
  } catch (erro) {
    console.error('❌ Erro ao criar doação:', erro);
    mostrarAlerta('Erro ao conectar com o servidor', 'error');
  }
}

function abrirModalEdicao(idCredito, qtdAtual) {
  showModalEditarDoacao(idCredito, qtdAtual);
  
  if (novaQtd === null) return;
  
  const quantidade = parseFloat(novaQtd);
  
  if (!quantidade || quantidade <= 0) {
    mostrarAlerta('Quantidade inválida', 'warning');
    return;
  }

  editarDoacao(idCredito, quantidade);
}

async function editarDoacao(idCredito, novaQuantidade) {
  try {
    const response = await fetch('/api/doador/doacao/editar', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id_credito: idCredito,
        quantidade_kwh: novaQuantidade
      })
    });

    const resultado = await response.json();

    if (resultado.sucesso) {
      mostrarAlerta('Doação atualizada com sucesso! ✅', 'success');
      await carregarDadosDoador();
    } else {
      mostrarAlerta(resultado.mensagem || 'Erro ao editar doação', 'error');
    }
  } catch (erro) {
    console.error('❌ Erro ao editar doação:', erro);
    mostrarAlerta('Erro ao conectar com o servidor', 'error');
  }
}

function confirmarExclusao(idCredito) {
  showModalExcluirDoacao(idCredito);
  
  if (confirmacao) {
    excluirDoacao(idCredito);
  }
}

function showModalEditarDoacao(idCredito, qtdAtual) {
  const modal = getOrCreateModal('modalEditarDoacao', `
    <div class="modal-overlay" id="modalEditarDoacao">
      <div class="modal-content">
        <div class="modal-header">
          <div class="modal-icon info">
            <i class="fas fa-edit"></i>
          </div>
          <div class="modal-header-text">
            <h2>Editar Doação</h2>
            <small>Doação #${idCredito}</small>
          </div>
        </div>
        <div class="modal-body">
          Quantidade atual: <strong>${qtdAtual} kWh</strong>
        </div>
        <div class="modal-input-group">
          <label>Nova quantidade (kWh):</label>
          <input type="number" id="inputNovaQuantidadeDoacao" step="0.01" value="${qtdAtual}">
        </div>
        <div class="modal-footer">
          <button class="modal-btn-secondary" onclick="closeModalInterativo('modalEditarDoacao')">
            <i class="fas fa-times"></i> Cancelar
          </button>
          <button class="modal-btn-primary" onclick="confirmarEditarDoacaoModal(${idCredito})">
            <i class="fas fa-save"></i> Salvar
          </button>
        </div>
      </div>
    </div>
  `);
  modal.classList.add('active');
}

function confirmarEditarDoacaoModal(idCredito) {
  const novaQtd = document.getElementById('inputNovaQuantidadeDoacao').value;
  closeModalInterativo('modalEditarDoacao');
  editarDoacao(idCredito, parseFloat(novaQtd));
}

function showModalExcluirDoacao(idCredito) {
  const modal = getOrCreateModal('modalExcluirDoacao', `
    <div class="modal-overlay" id="modalExcluirDoacao">
      <div class="modal-content">
        <div class="modal-header">
          <div class="modal-icon danger">
            <i class="fas fa-trash"></i>
          </div>
          <div class="modal-header-text">
            <h2>Excluir doação?</h2>
            <small>Doação #${idCredito}</small>
          </div>
        </div>
        <div class="modal-body">
          <strong>Atenção:</strong> Esta ação não pode ser desfeita. A doação será removida permanentemente do sistema.
        </div>
        <div class="modal-footer">
          <button class="modal-btn-secondary" onclick="closeModalInterativo('modalExcluirDoacao')">
            <i class="fas fa-times"></i> Cancelar
          </button>
          <button class="modal-btn-danger" onclick="confirmarExcluirDoacaoModal(${idCredito})">
            <i class="fas fa-trash"></i> Excluir Doação
          </button>
        </div>
      </div>
    </div>
  `);
  modal.classList.add('active');
}

function confirmarExcluirDoacaoModal(idCredito) {
  closeModalInterativo('modalExcluirDoacao');
  excluirDoacao(idCredito);
}

async function excluirDoacao(idCredito) {
  try {
    const response = await fetch('/api/doador/doacao/excluir', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_credito: idCredito })
    });

    const resultado = await response.json();

    if (resultado.sucesso) {
      mostrarAlerta('Doação excluída com sucesso! 🗑️', 'success');
      await carregarDadosDoador();
    } else {
      mostrarAlerta(resultado.mensagem || 'Erro ao excluir doação', 'error');
    }
  } catch (erro) {
    console.error('❌ Erro ao excluir doação:', erro);
    mostrarAlerta('Erro ao conectar com o servidor', 'error');
  }
}

function mostrarAlerta(mensagem, tipo = 'info') {
  const alertaExistente = document.querySelector('.alerta-flutuante');
  if (alertaExistente) {
    alertaExistente.remove();
  }

  const alerta = document.createElement('div');
  alerta.className = `alerta-flutuante alerta-${tipo}`;
  
  let icone = '📢';
  if (tipo === 'success') icone = '✅';
  else if (tipo === 'error') icone = '❌';
  else if (tipo === 'warning') icone = '⚠️';
  
  alerta.innerHTML = `
    <span class="alerta-icone">${icone}</span>
    <span class="alerta-mensagem">${mensagem}</span>
    <button class="alerta-fechar" onclick="this.parentElement.remove()">×</button>
  `;
  
  document.body.appendChild(alerta);
  
  setTimeout(() => {
    if (alerta.parentElement) {
      alerta.style.animation = 'slideOut 0.3s ease-out';
      setTimeout(() => alerta.remove(), 300);
    }
  }, 5000);
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