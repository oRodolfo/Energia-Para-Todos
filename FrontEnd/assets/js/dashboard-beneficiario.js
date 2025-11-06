document.addEventListener('DOMContentLoaded', async () => {
  await carregarDados();
  configurarModal();
});

async function carregarDados() {
  try {
    const resp = await fetch('/api/beneficiario/dados');
    const data = await resp.json();

    if (!data.sucesso) {
      alert(data.mensagem || 'Erro ao carregar dados');
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

    // Converte código do banco em um label legível e classe CSS
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
    // preserva a classe metric-value para manter o estilo das métricas
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
          <p style="color: #666; font-size: 0.95rem;">Clique em "Nova Solicitação de Créditos" para começar a ajudar!</p>
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
    alert('Erro ao carregar dados do beneficiário');
  }
}

async function editarSolicitacao(idFila, quantidadeAtual) {
  const novaQuantidade = prompt(
    `Editar solicitação\n\nQuantidade atual: ${quantidadeAtual} kWh\n\n⚠️ ATENÇÃO: Qualquer alteração joga sua solicitação para o FINAL DA FILA.\n\nDigite a nova quantidade:`, 
    quantidadeAtual
  );
  
  if (!novaQuantidade || parseFloat(novaQuantidade) <= 0) {
    return;
  }

  try {
    const resp = await fetch('/api/beneficiario/solicitacao/editar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id_fila: idFila,
        quantidade_kwh: parseFloat(novaQuantidade)
      })
    });

    const data = await resp.json();

    if (data.sucesso) {
      alert('✅ ' + data.mensagem + '\n\n⚠️ Sua posição na fila foi atualizada.');
      await carregarDados();
    } else {
      alert('❌ ' + data.mensagem);
    }
  } catch (err) {
    console.error('Erro:', err);
    alert('Erro de conexão com o servidor');
  }
}

// ✅ NOVA FUNÇÃO: EXCLUIR SOLICITAÇÃO
async function excluirSolicitacao(idFila) {
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
      alert('✅ ' + data.mensagem);
      await carregarDados();
    } else {
      alert('❌ ' + data.mensagem);
    }
  } catch (err) {
    console.error('Erro:', err);
    alert('Erro de conexão com o servidor');
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
    if (!kwh || kwh <= 0) {
      alert('Informe uma quantidade válida.');
      return;
    }

    // ✅ Validação de limite
    if (max > 0 && kwh > max) {
      alert(`Você só pode solicitar até ${max} kWh (seu consumo médio)`);
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
        alert(data.mensagem);
        modal.style.display = 'none';
        await carregarDados(); // ✅ Recarrega dados
      } else {
        alert(data.mensagem || 'Erro ao solicitar');
      }
    } catch (err) {
      console.error('Erro:', err);
      alert('Erro de conexão com o servidor');
    }
  };
}