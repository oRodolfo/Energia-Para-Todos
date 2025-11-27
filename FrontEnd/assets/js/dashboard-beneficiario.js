// ============================================
// DASHBOARD BENEFICIÁRIO - COM ALERTAS INTERATIVOS
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
  await carregarDados();
  configurarModal();
});

async function carregarDados() {
  try {
    const resp = await fetch('/api/beneficiario/dados');
    const data = await resp.json();

    if (!data.sucesso) {
      mostrarAlerta(data.mensagem || 'Erro ao carregar dados', 'error');
      return;
    }

    const d = data.dados;

    // ✅ Atualiza título com nome
    document.querySelector('.dashboard-title').textContent = `Olá, ${d.nome}!`;

    // ✅ Métricas
    document.getElementById('total-recebido').innerHTML = `${d.total_recebido_kwh || 0} <span>kWh</span>`;
    document.getElementById('consumo-medio').innerHTML = `${d.media_kwh || 0} <span>kWh</span>`;
    
    // ✅ STATUS formatado (label humano, ícone e cor)
    const statusEl = document.getElementById('status-solicitacao');
    const rawStatus = (d.descricao_status_beneficiario || '').toString();

    function formatStatus(code) {
      if (!code) return { label: '-', cls: 'status-desconhecido', icon: 'fa-question-circle' };
      const c = code.toUpperCase();
      if (c.includes('AGUARDANDO')) return { label: 'Aguardando Aprovação', cls: 'status-aguardando', icon: 'fa-clock' };
      if (c.includes('APROVADO')) return { label: 'Aprovado', cls: 'status-aprovado', icon: 'fa-check-circle' };
      if (c.includes('REJEITADO') || c.includes('RECUSADO')) return { label: 'Rejeitado', cls: 'status-rejeitado', icon: 'fa-times-circle' };
      const fallback = code.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, t => t.toUpperCase());
      return { label: fallback, cls: 'status-desconhecido', icon: 'fa-question-circle' };
    }

    const formatted = formatStatus(rawStatus);
    statusEl.className = 'metric-value';
    statusEl.innerHTML = `
      <div class="status-pill ${formatted.cls}" title="${formatted.label}">
        <i class="fas ${formatted.icon}" style="margin-right:10px;"></i>
        <span>${formatted.label}</span>
      </div>
    `;
    
    // ✅ Posição na fila DINÂMICA
    if (d.fila && d.fila.descricao_status_fila === 'AGUARDANDO') {
      document.getElementById('posicao-fila').textContent = `${d.fila.posicao_fila}º`;
    } else {
      document.getElementById('posicao-fila').textContent = 'Fora da fila';
    }

    // ✅ Atualiza limite no modal
    const consumoMax = d.media_kwh || 0;
    const alertDiv = document.querySelector('.modal-alert-info span');
    
    if (consumoMax > 0) {
      alertDiv.innerHTML = 
        `<b>Limite máximo:</b> ${consumoMax} kWh <span style="font-weight:400;">(seu consumo médio mensal)</span>`;
      alertDiv.parentElement.style.display = 'flex';
    } else {
      alertDiv.parentElement.style.display = 'none';
    }
    
    document.getElementById('input-kwh-solicitado').setAttribute('max', consumoMax);

    // ✅ Renderiza histórico com filtros
    renderizarHistoricoComFiltros(d.historico);
  } catch (err) {
    console.error('Erro:', err);
    mostrarAlerta('Erro ao carregar dados do beneficiário', 'error');
  }
}

// ✅ FUNÇÃO EDITAR SOLICITAÇÃO
async function editarSolicitacao(idFila, quantidadeAtual) {
  const novaQuantidade = prompt(
    `Editar solicitação\n\nQuantidade atual: ${quantidadeAtual} kWh\n\n⚠️ ATENÇÃO: Qualquer alteração joga sua solicitação para o FINAL DA FILA.\n\nDigite a nova quantidade:`, 
    quantidadeAtual
  );
  
  if (novaQuantidade === null) return; // Cancelou
  
  const qtd = parseFloat(novaQuantidade);
  
  if (!qtd || qtd <= 0 || isNaN(qtd)) {
    mostrarAlerta('Por favor, digite uma quantidade válida', 'warning');
    return;
  }

  try {
    const resp = await fetch('/api/beneficiario/solicitacao/editar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id_fila: idFila,
        quantidade_kwh: qtd // ✅ Garante que seja número válido
      })
    });

    const data = await resp.json();

    if (data.sucesso) {
      mostrarAlerta('✅ ' + data.mensagem, 'success');
      await carregarDados();
    } else {
      mostrarAlerta('❌ ' + data.mensagem, 'error');
    }
  } catch (err) {
    console.error('Erro:', err);
    mostrarAlerta('Erro de conexão com o servidor', 'error');
  }
}

// ✅ FUNÇÃO EXCLUIR SOLICITAÇÃO - COM ALERTA INTERATIVO
async function excluirSolicitacao(idFila) {
  // ✅ Usa confirm nativo (mais seguro para confirmação de exclusão)
  if (!confirm('⚠️ Tem certeza que deseja CANCELAR esta solicitação?\n\nEsta ação não pode ser desfeita.')) {
    return;
  }

  try {
    const resp = await fetch('/api/beneficiario/solicitacao/excluir', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_fila: idFila })
    });

    const data = await resp.json();

    if (data.sucesso) {
      mostrarAlerta('✅ ' + data.mensagem, 'success');
      await carregarDados();
    } else {
      mostrarAlerta('❌ ' + data.mensagem, 'error');
    }
  } catch (err) {
    console.error('Erro:', err);
    mostrarAlerta('Erro de conexão com o servidor', 'error');
  }
}

function configurarModal() {
  const modal = document.getElementById('modal-solicitacao');
  const btnAbrir = document.getElementById('btn-abrir-modal');
  const btnFechar = document.getElementById('btn-fechar-modal');
  const btnConfirmar = document.getElementById('btn-confirmar-solicitacao');
  const inputKwh = document.getElementById('input-kwh-solicitado');

  btnAbrir.onclick = () => {
    modal.style.display = 'flex';
    inputKwh.value = '';
  };

  btnFechar.onclick = () => {
    modal.style.display = 'none';
  };

  btnConfirmar.onclick = async () => {
    const kwh = parseFloat(inputKwh.value);
    const max = parseFloat(inputKwh.getAttribute('max')) || Infinity;

    // ✅ Validação de quantidade
    if (!kwh || kwh <= 0 || isNaN(kwh)) {
      mostrarAlerta('Informe uma quantidade válida.', 'warning');
      return;
    }

    // ✅ Validação de limite
    if (max > 0 && kwh > max) {
      mostrarAlerta(`Você só pode solicitar até ${max} kWh (seu consumo médio)`, 'warning');
      return;
    }

    try {
      const resp = await fetch('/api/beneficiario/solicitar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `quantidade_kwh=${kwh}`
      });

      const data = await resp.json();

      if (data.sucesso) {
        mostrarAlerta('✅ ' + data.mensagem, 'success');
        modal.style.display = 'none';
        await carregarDados();
      } else {
        mostrarAlerta('❌ ' + (data.mensagem || 'Erro ao solicitar'), 'error');
      }
    } catch (err) {
      console.error('Erro:', err);
      mostrarAlerta('Erro de conexão com o servidor', 'error');
    }
  };
}

// ============================================
// SISTEMA DE ALERTAS INTERATIVOS (IGUAL AO DOADOR)
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

// Variável para armazenar filtros ativos
let filtrosSolicitacoes = {
  status: 'TODOS',
  dataInicio: null,
  dataFim: null,
  quantidadeMin: null,
  quantidadeMax: null
};

// Dados originais (sem filtro)
let solicitacoesOriginais = [];

// RENDERIZAR HISTÓRICO COM FILTROS
function renderizarHistoricoComFiltros(historico) {
  // Salva dados originais
  solicitacoesOriginais = historico || [];
  
  const historicoDiv = document.getElementById('historico-solicitacoes');
  
  if (!historico || historico.length === 0) {
    historicoDiv.innerHTML = `
      <div style="text-align: center; padding: 40px 20px;">
        <i class="fas fa-inbox" style="font-size: 3rem; color: #ff9500; opacity: 0.3; margin-bottom: 15px;"></i>
        <p style="color: #999; font-size: 1.1rem; margin-bottom: 10px;">Nenhuma solicitação registrada ainda.</p>
        <p style="color: #666; font-size: 0.95rem;">Clique em "Nova Solicitação de Créditos" para começar!</p>
      </div>
    `;
    return;
  }

  // Aplicar filtros
  let historicoFiltrado = aplicarFiltrosSolicitacoes(historico);

  // Header com filtros
  let html = `
    <div class="filtros-container">
      <div class="filtros-header">
        <span class="filtros-titulo">
          <i class="fas fa-filter"></i> Filtros
        </span>
        <button class="btn-limpar-filtros" onclick="limparFiltrosSolicitacoes()" title="Limpar todos os filtros">
          <i class="fas fa-times"></i> Limpar
        </button>
      </div>
      
      <div class="filtros-grid">
        <!-- Filtro de Status -->
        <div class="filtro-item">
          <label class="filtro-label">
            <i class="fas fa-circle-check"></i> Status da Solicitação
          </label>
          <select class="filtro-select" id="filtro-status-solicitacao" onchange="atualizarFiltroStatusSolicitacao(this.value)">
            <option value="TODOS">Todos os Status</option>
            <option value="AGUARDANDO">⏳ Aguardando</option>
            <option value="ATENDIDO">✅ Atendido</option>
            <option value="CANCELADO">❌ Cancelado</option>
          </select>
        </div>

        <!-- Filtro de Data -->
        <div class="filtro-item">
          <label class="filtro-label">
            <i class="fas fa-calendar"></i> Data da Solicitação
          </label>
          <div class="filtro-data-group">
            <input type="date" class="filtro-input" id="filtro-data-inicio-solicitacao" 
                   onchange="atualizarFiltroDataSolicitacao()" placeholder="De">
            <span class="filtro-separador">até</span>
            <input type="date" class="filtro-input" id="filtro-data-fim-solicitacao" 
                   onchange="atualizarFiltroDataSolicitacao()" placeholder="Até">
          </div>
        </div>

        <!-- Filtro de Quantidade -->
        <div class="filtro-item">
          <label class="filtro-label">
            <i class="fas fa-bolt"></i> Quantidade Solicitada (kWh)
          </label>
          <div class="filtro-data-group">
            <input type="number" class="filtro-input" id="filtro-qtd-min-solicitacao" 
                   onchange="atualizarFiltroQuantidadeSolicitacao()" placeholder="Mínimo" step="0.01">
            <span class="filtro-separador">até</span>
            <input type="number" class="filtro-input" id="filtro-qtd-max-solicitacao" 
                   onchange="atualizarFiltroQuantidadeSolicitacao()" placeholder="Máximo" step="0.01">
          </div>
        </div>
      </div>

      <div class="filtros-info">
        <span class="filtros-resultado">
          <i class="fas fa-list"></i> 
          Mostrando <strong>${historicoFiltrado.length}</strong> de <strong>${historico.length}</strong> solicitações
        </span>
      </div>
    </div>
  `;

  // Verificar se há resultados após filtro
  if (historicoFiltrado.length === 0) {
    html += `
      <div class="empty-state">
        <i class="fas fa-search"></i>
        <p>Nenhuma solicitação encontrada com os filtros aplicados</p>
        <p class="empty-state-hint">Tente ajustar os filtros ou clique em "Limpar"</p>
      </div>
    `;
    historicoDiv.innerHTML = html;
    return;
  }

  // Tabela com dados filtrados
  html += `
    <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
      <thead>
        <tr style="background: rgba(255, 149, 0, 0.1); text-align: left;">
          <th style="padding: 12px; border-bottom: 2px solid #ff9500;">Data</th>
          <th style="padding: 12px; border-bottom: 2px solid #ff9500;">Quantidade (kWh)</th>
          <th style="padding: 12px; border-bottom: 2px solid #ff9500;">Posição na Fila</th>
          <th style="padding: 12px; border-bottom: 2px solid #ff9500;">Foi Atendido?</th>
          <th style="padding: 12px; border-bottom: 2px solid #ff9500; text-align: center;">Ações</th>
        </tr>
      </thead>
      <tbody>
  `;

  historicoFiltrado.forEach(h => {
    const dataFormatada = new Date(h.data_transacao).toLocaleDateString('pt-BR');
    
    let statusClass = 'aguardando';
    let statusText = 'NÃO';
    
    if (h.foi_atendido === 'SIM') {
      statusClass = 'atendido';
      statusText = 'SIM ✓';
    } else if (h.foi_atendido === 'CANCELADO') {
      statusClass = 'cancelado';
      statusText = 'CANCELADO';
    }
    
    const posicaoTexto = h.descricao_status === 'AGUARDANDO' 
      ? `${h.posicao_fila || '-'}º`
      : '-';
    
    // Botões de ação (só aparece se AGUARDANDO)
    const botoesAcao = h.descricao_status === 'AGUARDANDO' ? `
      <button class="btn-acao btn-editar" onclick="editarSolicitacao(${h.id_fila}, ${h.quantidade_kwh})" title="Editar Solicitação">
        <i class="fas fa-edit"></i>
      </button>
      <button class="btn-acao btn-excluir" onclick="excluirSolicitacao(${h.id_fila})" title="Cancelar Solicitação">
        <i class="fas fa-trash"></i>
      </button>
    ` : '<span style="color: #666;">-</span>';
    
    html += `
      <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.1); transition: background 0.3s;">
        <td style="padding: 12px;">${dataFormatada}</td>
        <td style="padding: 12px; font-weight: bold; color: #ffd34d;">${h.quantidade_kwh} kWh</td>
        <td style="padding: 12px;">${posicaoTexto}</td>
        <td style="padding: 12px;">
          <span class="status-badge ${statusClass}">${statusText}</span>
        </td>
        <td style="padding: 12px; text-align: center;">
          <div style="display: flex; gap: 8px; justify-content: center;">
            ${botoesAcao}
          </div>
        </td>
      </tr>
    `;
  });

  html += '</tbody></table>';
  historicoDiv.innerHTML = html;

  // Restaurar valores dos filtros nos inputs
  restaurarValoresFiltrosSolicitacoes();
}

// APLICAR FILTROS
function aplicarFiltrosSolicitacoes(historico) {
  return historico.filter(solicitacao => {
    // Filtro de Status
    if (filtrosSolicitacoes.status !== 'TODOS') {
      // Mapeia o status descritivo para o status da solicitação
      if (filtrosSolicitacoes.status === 'AGUARDANDO' && solicitacao.descricao_status !== 'AGUARDANDO') {
        return false;
      }
      if (filtrosSolicitacoes.status === 'ATENDIDO' && solicitacao.foi_atendido !== 'SIM') {
        return false;
      }
      if (filtrosSolicitacoes.status === 'CANCELADO' && solicitacao.foi_atendido !== 'CANCELADO') {
        return false;
      }
    }

    // Filtro de Data
    if (filtrosSolicitacoes.dataInicio || filtrosSolicitacoes.dataFim) {
      const dataSolicitacao = new Date(solicitacao.data_transacao);
      
      if (filtrosSolicitacoes.dataInicio) {
        const dataInicio = new Date(filtrosSolicitacoes.dataInicio);
        if (dataSolicitacao < dataInicio) return false;
      }
      
      if (filtrosSolicitacoes.dataFim) {
        const dataFim = new Date(filtrosSolicitacoes.dataFim);
        if (dataSolicitacao > dataFim) return false;
      }
    }

    // Filtro de Quantidade
    const quantidade = parseFloat(solicitacao.quantidade_kwh || 0);
    
    if (filtrosSolicitacoes.quantidadeMin !== null) {
      if (quantidade < filtrosSolicitacoes.quantidadeMin) return false;
    }
    
    if (filtrosSolicitacoes.quantidadeMax !== null) {
      if (quantidade > filtrosSolicitacoes.quantidadeMax) return false;
    }

    return true;
  });
}

// ATUALIZAR FILTRO DE STATUS
function atualizarFiltroStatusSolicitacao(status) {
  filtrosSolicitacoes.status = status;
  renderizarHistoricoComFiltros(solicitacoesOriginais);
  mostrarAlerta(`Filtro aplicado: ${status === 'TODOS' ? 'Todos os status' : status}`, 'info');
}

// ATUALIZAR FILTRO DE DATA
function atualizarFiltroDataSolicitacao() {
  const dataInicio = document.getElementById('filtro-data-inicio-solicitacao').value;
  const dataFim = document.getElementById('filtro-data-fim-solicitacao').value;
  
  filtrosSolicitacoes.dataInicio = dataInicio || null;
  filtrosSolicitacoes.dataFim = dataFim || null;
  
  renderizarHistoricoComFiltros(solicitacoesOriginais);
  
  if (dataInicio || dataFim) {
    mostrarAlerta('Filtro de data aplicado', 'info');
  }
}

// ATUALIZAR FILTRO DE QUANTIDADE
function atualizarFiltroQuantidadeSolicitacao() {
  const qtdMin = document.getElementById('filtro-qtd-min-solicitacao').value;
  const qtdMax = document.getElementById('filtro-qtd-max-solicitacao').value;
  
  filtrosSolicitacoes.quantidadeMin = qtdMin ? parseFloat(qtdMin) : null;
  filtrosSolicitacoes.quantidadeMax = qtdMax ? parseFloat(qtdMax) : null;
  
  renderizarHistoricoComFiltros(solicitacoesOriginais);
  
  if (qtdMin || qtdMax) {
    mostrarAlerta('Filtro de quantidade aplicado', 'info');
  }
}

// LIMPAR TODOS OS FILTROS
function limparFiltrosSolicitacoes() {
  filtrosSolicitacoes = {
    status: 'TODOS',
    dataInicio: null,
    dataFim: null,
    quantidadeMin: null,
    quantidadeMax: null
  };
  
  // Limpar inputs
  const selectStatus = document.getElementById('filtro-status-solicitacao');
  const inputDataInicio = document.getElementById('filtro-data-inicio-solicitacao');
  const inputDataFim = document.getElementById('filtro-data-fim-solicitacao');
  const inputQtdMin = document.getElementById('filtro-qtd-min-solicitacao');
  const inputQtdMax = document.getElementById('filtro-qtd-max-solicitacao');
  
  if (selectStatus) selectStatus.value = 'TODOS';
  if (inputDataInicio) inputDataInicio.value = '';
  if (inputDataFim) inputDataFim.value = '';
  if (inputQtdMin) inputQtdMin.value = '';
  if (inputQtdMax) inputQtdMax.value = '';
  
  renderizarHistoricoComFiltros(solicitacoesOriginais);
  mostrarAlerta('Filtros limpos! Mostrando todas as solicitações', 'success');
}

// RESTAURAR VALORES DOS FILTROS
function restaurarValoresFiltrosSolicitacoes() {
  const selectStatus = document.getElementById('filtro-status-solicitacao');
  const inputDataInicio = document.getElementById('filtro-data-inicio-solicitacao');
  const inputDataFim = document.getElementById('filtro-data-fim-solicitacao');
  const inputQtdMin = document.getElementById('filtro-qtd-min-solicitacao');
  const inputQtdMax = document.getElementById('filtro-qtd-max-solicitacao');

  if (selectStatus) selectStatus.value = filtrosSolicitacoes.status;
  if (inputDataInicio) inputDataInicio.value = filtrosSolicitacoes.dataInicio || '';
  if (inputDataFim) inputDataFim.value = filtrosSolicitacoes.dataFim || '';
  if (inputQtdMin) inputQtdMin.value = filtrosSolicitacoes.quantidadeMin || '';
  if (inputQtdMax) inputQtdMax.value = filtrosSolicitacoes.quantidadeMax || '';
}
