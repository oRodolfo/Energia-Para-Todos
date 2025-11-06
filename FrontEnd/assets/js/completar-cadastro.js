// /assets/js/completar-cadastro.js
document.addEventListener('DOMContentLoaded', () => {
  init();
});

async function init() {
  try {
    const form      = document.getElementById('form-cadastro');
    const camposDiv = document.getElementById('campos-dinamicos');
    const titulo    = document.getElementById('titulo-cadastro');
    const subtitulo = document.getElementById('subtitulo-cadastro');

    // 1) Buscar dados do usuário
    console.log('Buscando perfil do usuário...');
    const meResp = await fetch('/api/meu-perfil');
    
    if (meResp.status === 401) {
      console.log('Usuário não autenticado, redirecionando...');
      alert('Sua sessão expirou. Faça login novamente.');
      window.location.href = '/login';
      return;
    }
    
    if (!meResp.ok) {
      throw new Error(`Erro HTTP: ${meResp.status}`);
    }
    
    const me = await meResp.json();
    console.log('Perfil recebido:', me);

    if (!me.sucesso) {
      console.log('Erro na resposta:', me.mensagem);
      alert(me.mensagem || 'Erro ao carregar perfil');
      window.location.href = me.redirect || '/login';
      return;
    }

    // 2) Verificar se usuário está logado
    if (!me || !me.usuario_id) {
      alert('Usuário não autenticado. Faça login novamente.');
      location.href = '/login';
      return;
    }

    // 3) Construir interface baseada no tipo
    const tipo = me?.tipo;

    // Se ainda não tem tipo, mostrar seleção
    if (!tipo || tipo === 'null' || tipo === null) {
      mostrarSelecaoPerfil(me, camposDiv, form);
    } else if (tipo === 'DOADOR') {
      mostrarFormularioDoador(me, camposDiv, form, titulo, subtitulo);
    } else if (tipo === 'BENEFICIARIO') {
      mostrarFormularioBeneficiario(me, camposDiv, form, titulo, subtitulo);
    } else {
      alert('Tipo de perfil inválido.');
    }

  } catch (err) {
    console.error('Erro ao inicializar página:', err);
    alert('Falha ao carregar a página. Verifique o console (F12).');
  }
}

// ========================================
// SELEÇÃO DE PERFIL (se ainda não definiu)
// ========================================
function mostrarSelecaoPerfil(me, camposDiv, form) {
  document.getElementById('titulo-cadastro').textContent = 'Escolha seu Perfil';
  document.getElementById('subtitulo-cadastro').textContent = 'Você deseja ser Doador ou Beneficiário?';

  camposDiv.innerHTML = `
    <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
      <button type="button" id="btn-doador" class="btn" style="flex: 1;">
        🌞 Sou Doador
      </button>
      <button type="button" id="btn-beneficiario" class="btn" style="flex: 1; background: linear-gradient(135deg, #00d4ff, #0099cc);">
        🏠 Sou Beneficiário
      </button>
    </div>
  `;

  // Esconder botão de submit
  form.querySelector('button[type="submit"]').style.display = 'none';

  // Eventos dos botões
  document.getElementById('btn-doador').onclick = async () => {
    await definirPerfil('DOADOR');
  };

  document.getElementById('btn-beneficiario').onclick = async () => {
    await definirPerfil('BENEFICIARIO');
  };
}

async function definirPerfil(tipo) {
  try {
    const resp = await fetch('/api/perfil/escolher', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tipo })
    });

    const data = await resp.json();

    if (data.sucesso) {
      location.reload(); // Recarrega para mostrar formulário correto
    } else {
      alert(data.mensagem || 'Erro ao definir perfil');
    }
  } catch (err) {
    alert('Erro de conexão');
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
  const cnpjEl  = document.getElementById('cnpj');

  // Mostrar/ocultar campos PJ
  const togglePJ = () => {
    if (classEl.value === 'PESSOA_JURIDICA') {
      grupoPJ.classList.remove('cc-hide');
    } else {
      grupoPJ.classList.add('cc-hide');
    }
  };

  classEl.addEventListener('change', togglePJ);
  togglePJ();

  // Máscara de CNPJ
  if (cnpjEl) {
    cnpjEl.addEventListener('input', () => {
      let v = cnpjEl.value.replace(/[^\d]/g, '').slice(0, 14);
      if (v.length >= 3)  v = v.replace(/^(\d{2})(\d)/, '$1.$2');
      if (v.length >= 6)  v = v.replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3');
      if (v.length >= 9)  v = v.replace(/^(\d{2})\.(\d{3})\.(\d{3})(\d)/, '$1.$2.$3/$4');
      if (v.length >= 13) v = v.replace(/^(\d{2})\.(\d{3})\.(\d{3})\/(\d{4})(\d)/, '$1.$2.$3/$4-$5');
      cnpjEl.value = v;
    });
  }

  // Submit
  form.onsubmit = async (e) => {
    e.preventDefault();

    const classificacao = classEl.value;
    const payload = new URLSearchParams();
    payload.append('classificacao', classificacao);

    if (classificacao === 'PESSOA_JURIDICA') {
      const razao = (document.getElementById('razao_social').value || '').trim();
      const cnpj  = (document.getElementById('cnpj').value || '').replace(/[^\d]/g, '');
      
      if (!razao || !cnpj || cnpj.length !== 14) {
        alert('Informe Razão Social e CNPJ válido (14 dígitos).');
        return;
      }
      
      payload.append('razao_social', razao);
      payload.append('cnpj', cnpj);
    }

    try {
      const resp = await fetch('/api/perfil/completar/doador', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          classificacao,
          razao_social: classificacao === 'PESSOA_JURIDICA' ? razao : undefined,
          cnpj: classificacao === 'PESSOA_JURIDICA' ? cnpj : undefined
        })
      });

      const data = await resp.json();

      if (data.sucesso) {
        alert('Cadastro completo!');
        location.href = data.redirect || '/painel-doador';
      } else {
        alert(data.mensagem || 'Erro ao salvar.');
      }
    } catch (err) {
      console.error(err);
      alert('Erro de conexão com o servidor.');
    }
  };
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

  // Submit
  form.onsubmit = async (e) => {
    e.preventDefault();

    const payload = new URLSearchParams(new FormData(form));

    try {
      const formData = Object.fromEntries(payload);
      const resp = await fetch('/api/perfil/completar/beneficiario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          renda_mensal: parseFloat(formData.renda_familiar),
          consumo_medio_kwh: parseFloat(formData.consumo_medio_kwh),
          num_moradores: parseInt(formData.num_moradores)
        })
      });

      const data = await resp.json();

      if (data.sucesso) {
        alert('Cadastro completo!');
        location.href = data.redirect || '/painel-beneficiario';
      } else {
        alert(data.mensagem || 'Erro ao salvar.');
      }
    } catch (err) {
      console.error(err);
      alert('Erro de conexão com o servidor.');
    }
  };
}