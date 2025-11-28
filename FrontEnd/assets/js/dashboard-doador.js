// DASHBOARD DOADOR - VERSÃO ATUALIZADA
let dadosDoador = null;

// INICIALIZAÇÃO
document.addEventListener('DOMContentLoaded', async () => {
  console.log('🚀 Dashboard Doador iniciado');
  await carregarDadosDoador();
  configurarEventos();
  configurarModalEdicao();
  configurarNavegacao(); // Nova função
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
    
    // Determina o nome de exibição
    let nomeExibicao = dados.nome;

    if (dados.classificacao === 'PESSOA_JURIDICA' && dados.razao_social) {
      nomeExibicao = dados.razao_social;
    }
    
    // Atualiza o título
    document.querySelector('.dashboard-title').textContent = `Olá, ${nomeExibicao}`;

    // Atualizar subtítulo com classificação
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
    const status = credito.descricao_status || 'DESCONHECIDO';
    const dataExpiracao = credito.data_expiracao 
      ? new Date(credito.data_expiracao).toLocaleDateString('pt-BR')
      : 'Sem data';

    const podeEditar = qtdConsumida === 0;
    
    let statusClass = 'status-info';
    if (status === 'DISPONIVEL') statusClass = 'status-success';
    else if (status === 'ESGOTADO') statusClass = 'status-danger';
    else if (status === 'PARCIALMENTE_UTILIZADO') statusClass = 'status-warning';

    html += `
      <tr>
        <td><span class="badge badge-primary">⚡ #${credito.id_credito}</span></td>
        <td>${qtdInicial.toFixed(2)} kWh</td>
        <td>${qtdDisponivel.toFixed(2)} kWh</td>
        <td>${qtdConsumida.toFixed(2)} kWh</td>
        <td><span class="badge ${statusClass}">${status}</span></td>
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
        <span class="badge badge-info" title="Esta doação já foi distribuída e não pode ser alterada">
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
    if (filtrosAtivos.status !== 'TODOS') {
      if (credito.descricao_status !== filtrosAtivos.status) {
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

  // NOVA FUNCIONALIDADE: Navegação
  configurarNavegacao();
}

// NOVA FUNÇÃO: CONFIGURAR NAVEGAÇÃO
function configurarNavegacao() {
  const btnInicio = document.getElementById('btn-inicio');
  const btnEditar = document.getElementById('btn-editar');
  const btnLogout = document.getElementById('btn-logout');

  // Botão Página Inicial
  btnInicio?.addEventListener('click', () => {
    window.location.href = '/index.html';
  });

  // Botão Editar Perfil
  btnEditar?.addEventListener('click', () => {
    const modal = document.getElementById('modal-editar-perfil');
    if (modal) {
      carregarDadosParaEdicao();
      modal.classList.add('show');
    } else {
      // fallback
      window.location.href = '/editar-perfil-doador';
    }
  });

  // Botão Logout
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
        // Mesmo com erro, redireciona para o login
        window.location.href = '/login';
      }
    }
  });
}

// --------------------------------------------------
// Modal de edição / Perfil do Doador
// --------------------------------------------------
function configurarModalEdicao() {
  const modal = document.getElementById('modal-editar-perfil');
  const btnFechar = document.getElementById('btn-fechar-modal-editar');
  const btnSalvar = document.getElementById('btn-salvar-perfil');
  const form = document.getElementById('form-editar-perfil');

  // Injeta opção para alterar senha (uma vez)
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

  // Salvar via submit para permitir Enter
  form?.addEventListener('submit', (ev) => {
    ev.preventDefault();
    salvarEdicaoPerfil();
  });

  btnSalvar?.addEventListener('click', (ev) => {
    ev.preventDefault();
    salvarEdicaoPerfil();
  });

  // Fechar ao clicar fora
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

    if (data.sucesso) {
      document.getElementById('input-nome').value = data.nome || '';
      document.getElementById('input-email').value = data.email || '';
    }

    // Preenche dados do doador se necessário
    const respDoador = await fetch('/api/doador/dados', { credentials: 'include' });
    const dataDoador = await respDoador.json();
    // Pode-se preencher campos específicos do doador aqui no futuro

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

    // Atualizar nome/email
    const formBody = `nome=${encodeURIComponent(nome)}&email=${encodeURIComponent(email)}`;

    await fetch('/usuario/atualizar-dados', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formBody
    });

    // Alterar senha opcional
    if (alterarSenha) {
      if (!senhaAtual || !senhaNova || senhaNova.length < 6) {
        mostrarAlerta('Preencha corretamente as senhas (nova mínimo 6 caracteres).', 'warning');
        return;
      }

      const senhaBody = `login=${encodeURIComponent(email)}&senha_atual=${encodeURIComponent(senhaAtual)}&senha_nova=${encodeURIComponent(senhaNova)}`;

      const resp = await fetch('/usuario/alterar-senha', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: senhaBody
      });

      const resJson = await resp.json();
      if (!resJson.sucesso) {
        mostrarAlerta(resJson.mensagem || 'Erro ao alterar senha', 'error');
        return;
      }
    }

    mostrarAlerta('✓ Perfil atualizado com sucesso!', 'success');
    document.getElementById('modal-editar-perfil').classList.remove('show');

    // Recarregar dados no painel
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

// CRIAR NOVA DOAÇÃO
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

// EDITAR DOAÇÃO
function abrirModalEdicao(idCredito, qtdAtual) {
  const novaQtd = prompt(`Editar Doação #${idCredito}\n\nQuantidade atual: ${qtdAtual} kWh\nNova quantidade (kWh):`, qtdAtual);
  
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

// EXCLUIR DOAÇÃO
function confirmarExclusao(idCredito) {
  const confirmacao = confirm(`ATENÇÃO!\n\nDeseja realmente EXCLUIR a doação #${idCredito}?\n\nEsta ação não pode ser desfeita.`);
  
  if (confirmacao) {
    excluirDoacao(idCredito);
  }
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

// SISTEMA DE ALERTAS
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