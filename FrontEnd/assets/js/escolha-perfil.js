document.addEventListener("DOMContentLoaded", function() {
  let tipoSelecionado = null;
  const btnContinuar = document.getElementById('btn-continuar');
  const cardDoador = document.getElementById('card-doador');
  const cardBeneficiario = document.getElementById('card-beneficiario');

  function selecionar(tipo) {
    tipoSelecionado = tipo;
    btnContinuar.disabled = false;
    cardDoador.classList.remove('selected');
    cardBeneficiario.classList.remove('selected');
    if (tipo === 'DOADOR') cardDoador.classList.add('selected');
    if (tipo === 'BENEFICIARIO') cardBeneficiario.classList.add('selected');
  }

  cardDoador.onclick = () => selecionar('DOADOR');
  cardBeneficiario.onclick = () => selecionar('BENEFICIARIO');
  cardDoador.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') selecionar('DOADOR'); };
  cardBeneficiario.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') selecionar('BENEFICIARIO'); };

  btnContinuar.onclick = async function() {
    if (!tipoSelecionado) {
      if (window.showModalAlert) {
        await window.showModalAlert({ 
          title: '⚠️ Atenção', 
          message: 'Por favor, selecione um perfil antes de continuar.', 
          type: 'warning' 
        });
      }
      return;
    }

    btnContinuar.disabled = true;
    btnContinuar.textContent = "Processando...";

    try {
      // ✅ CHAMADA CORRIGIDA: Usa a API para definir o perfil
      const resp = await fetch('/api/perfil/escolher', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          tipo: tipoSelecionado
        })
      });

      const data = await resp.json();

      if (data.sucesso) {
        // ✅ REDIRECIONAMENTO AUTOMÁTICO para completar-cadastro
        if (window.showModalAlert) {
          await window.showModalAlert({ 
            title: '✅ Perfil Selecionado', 
            message: `Você escolheu ser ${tipoSelecionado === 'DOADOR' ? 'Doador' : 'Beneficiário'}! Vamos completar seu cadastro.`,
            type: 'success',
            onClose: () => {
              window.location.href = '/completar-cadastro';
            }
          });
        } else {
          window.location.href = '/completar-cadastro';
        }
      } else {
        if (window.showModalAlert) {
          await window.showModalAlert({ 
            title: '❌ Erro', 
            message: data.mensagem || 'Erro ao definir perfil. Tente novamente.', 
            type: 'error'
          });
        }
        btnContinuar.disabled = false;
        btnContinuar.textContent = "Continuar →";
      }

    } catch (e) {
      console.error('Erro:', e);
      if (window.showModalAlert) {
        await window.showModalAlert({ 
          title: '⚠️ Erro de conexão', 
          message: 'Não foi possível conectar ao servidor. Verifique se o servidor está rodando e tente novamente.', 
          type: 'error' 
        });
      }
      btnContinuar.disabled = false;
      btnContinuar.textContent = "Continuar →";
    }
  };
});