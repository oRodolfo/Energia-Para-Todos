// /assets/js/escolha-perfil.js

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

  // Botão continuar
  btnContinuar.onclick = async function() {
    if (!tipoSelecionado) {
      alert("Selecione um perfil antes de continuar.");
      return;
    }

    btnContinuar.disabled = true;
    btnContinuar.textContent = "Processando...";

    try {
      // Envia exatamente no formato que o backend espera
      const resp = await fetch('/api/perfil/escolher', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tipo: tipoSelecionado })
      });

      if (!resp.ok && resp.status === 401) {
        // Se não estiver autenticado, redireciona para o login
        window.location.href = '/login';
        return;
      }

      const data = await resp.json();

      if (data.sucesso) {
        if (data.mensagem) {
          alert(data.mensagem);
        }
        // redireciona de acordo com o backend ou para a página padrão
        window.location.href = data.redirect || '/completar-cadastro';
      } else {
        alert(data.mensagem || "Erro ao definir perfil.");
        if (data.redirect) {
          window.location.href = data.redirect;
        } else {
          btnContinuar.disabled = false;
          btnContinuar.textContent = "Continuar →";
        }
      }

    } catch (e) {
      alert('Erro de conexão com o servidor.');
      btnContinuar.disabled = false;
      btnContinuar.textContent = "Continuar →";
    }
  };
});