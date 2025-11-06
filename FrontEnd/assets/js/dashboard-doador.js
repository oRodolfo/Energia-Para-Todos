// ============================================
// DASHBOARD DOADOR - COM CRUD COMPLETO
// ============================================

let dadosDoador = null;

// ============================================
// INICIALIZAÇÃO
// ============================================
document.addEventListener('DOMContentLoaded', async () => {
  console.log('🚀 Dashboard Doador iniciado');
  await carregarDadosDoador();
  configurarEventos();
});

// ============================================
// CARREGAR DADOS DO DOADOR
// ============================================
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

    dadosDoador = resultado.dados;
    renderizarDashboard(dadosDoador);
    
  } catch (erro) {
    console.error('❌ Erro ao carregar dados:', erro);
    mostrarAlerta('Erro ao conectar com o servidor', 'error');
  }
}

// ============================================
// RENDERIZAR DASHBOARD
// ============================================
function renderizarDashboard(dados) {
  console.log('📊 Renderizando dashboard:', dados);

  // Atualizar título com nome do doador
  document.querySelector('.dashboard-title').textContent = `Olá, ${dados.nome}!`;

  // Atualizar métricas
  document.getElementById('total-doado').innerHTML = 
    `${dados.total_doado_kwh || 0} <span>kWh</span>`;
  
  document.getElementById('total-distribuido').innerHTML = 
    `${dados.total_distribuido_kwh || 0} <span>kWh</span>`;
  
  document.getElementById('familias-atendidas').textContent = 
    dados.familias_atendidas || 0;
  
  document.getElementById('co2-reduzido').innerHTML = 
    `${dados.co2_reduzido_kg || 0} <span>kg</span>`;

  // Renderizar histórico de doações
  renderizarHistorico(dados.creditos || []);
}

// ============================================
// RENDERIZAR HISTÓRICO COM BOTÕES CRUD
// ============================================
function renderizarHistorico(creditos) {
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

  // Criar tabela com ações CRUD
  let html = `
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

  creditos.forEach(credito => {
    const qtdInicial = parseFloat(credito.quantidade_inicial || 0);
    const qtdDisponivel = parseFloat(credito.quantidade_disponivel_kwh || 0);
    const qtdConsumida = parseFloat(credito.quantidade_consumida || 0);
    const status = credito.descricao_status || 'DESCONHECIDO';
    const dataExpiracao = credito.data_expiracao 
      ? new Date(credito.data_expiracao).toLocaleDateString('pt-BR')
      : 'Sem data';

    // ✅ Define se pode editar/excluir (somente se quantidade_consumida = 0)
    const podeEditar = qtdConsumida === 0;
    
    // Status badge
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
      // ✅ Pode editar e excluir
      html += `
        <button class="btn-action btn-edit" onclick="abrirModalEdicao(${credito.id_credito}, ${qtdInicial})" title="Editar doação">
          <i class="fas fa-edit"></i>
        </button>
        <button class="btn-action btn-delete" onclick="confirmarExclusao(${credito.id_credito})" title="Excluir doação">
          <i class="fas fa-trash"></i>
        </button>
      `;
    } else {
      // ❌ Não pode editar/excluir (já foi distribuído)
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
}

// ============================================
// CONFIGURAR EVENTOS
// ============================================
function configurarEventos() {
  // Modal Nova Doação
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

  // Fechar modal ao clicar fora
  modalOverlay?.addEventListener('click', (e) => {
    if (e.target === modalOverlay) {
      modalOverlay.style.display = 'none';
    }
  });
}

// ============================================
// CRIAR NOVA DOAÇÃO
// ============================================
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
      await carregarDadosDoador(); // Recarrega dashboard
    } else {
      mostrarAlerta(resultado.mensagem || 'Erro ao registrar doação', 'error');
    }
  } catch (erro) {
    console.error('❌ Erro ao criar doação:', erro);
    mostrarAlerta('Erro ao conectar com o servidor', 'error');
  }
}

// ============================================
// EDITAR DOAÇÃO
// ============================================
function abrirModalEdicao(idCredito, qtdAtual) {
  const novaQtd = prompt(`Editar Doação #${idCredito}\n\nQuantidade atual: ${qtdAtual} kWh\nNova quantidade (kWh):`, qtdAtual);
  
  if (novaQtd === null) return; // Cancelou
  
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

// ============================================
// EXCLUIR DOAÇÃO
// ============================================
function confirmarExclusao(idCredito) {
  const confirmacao = confirm(`⚠️ ATENÇÃO!\n\nDeseja realmente EXCLUIR a doação #${idCredito}?\n\nEsta ação não pode ser desfeita.`);
  
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

// ============================================
// SISTEMA DE ALERTAS
// ============================================
function mostrarAlerta(mensagem, tipo = 'info') {
  // Remove alertas existentes
  const alertaExistente = document.querySelector('.alerta-flutuante');
  if (alertaExistente) {
    alertaExistente.remove();
  }

  // Cria novo alerta
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
  
  // Remove automaticamente após 5 segundos
  setTimeout(() => {
    if (alerta.parentElement) {
      alerta.style.animation = 'slideOut 0.3s ease-out';
      setTimeout(() => alerta.remove(), 300);
    }
  }, 5000);
}