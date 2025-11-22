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

    // ✅ HISTÓRICO DE SOLICITAÇÕES (Tabela completa)
    const historicoDiv = document.getElementById('historico-solicitacoes');
    
    if (!d.historico || d.historico.length === 0) {
      historicoDiv.innerHTML = `
        <div style="text-align: center; padding: 40px 20px;">
          <i class="fas fa-inbox" style="font-size: 3rem; color: #ff9500; opacity: 0.3; margin-bottom: 15px;"></i>
          <p style="color: #999; font-size: 1.1rem; margin-bottom: 10px;">Nenhuma solicitação registrada ainda.</p>
          <p style="color: #666; font-size: 0.95rem;">Clique em "Nova Solicitação de Créditos" para começar!</p>
        </div>
      `;
    } else {
      historicoDiv.innerHTML = `
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
            ${d.historico.map(h => {
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
              
              // ✅ BOTÕES DE AÇÃO (só aparece se AGUARDANDO)
              const botoesAcao = h.descricao_status === 'AGUARDANDO' ? `
                <button class="btn-acao btn-editar" onclick="editarSolicitacao(${h.id_fila}, ${h.quantidade_kwh})" title="Editar Solicitação">
                  <i class="fas fa-edit"></i>
                </button>
                <button class="btn-acao btn-excluir" onclick="excluirSolicitacao(${h.id_fila})" title="Cancelar Solicitação">
                  <i class="fas fa-trash"></i>
                </button>
              ` : '<span style="color: #666;">-</span>';
              
              return `
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
            }).join('')}
          </tbody>
        </table>
      `;
    }

  } catch (err) {
    console.error('Erro:', err);
    mostrarAlerta('Erro ao carregar dados do beneficiário', 'error');
  }
}

// ✅ FUNÇÃO EDITAR SOLICITAÇÃO - CORRIGIDA
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