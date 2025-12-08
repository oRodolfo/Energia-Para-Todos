// Tarifa média de energia no Brasil (R$/kWh)
const TARIFA = 0.80;

// Geração diária por kW de placa solar (em kWh)
const GERACAO_DIA = { 3: 12, 5: 20, 10: 40 };

document.addEventListener('DOMContentLoaded', inicializar);

function inicializar() {
    criarInterfacePassoAPassoCompleta();
    criarEstilosModal();
    atualizar(); // inicial
}

function criarEstilosModal() {
    const style = document.createElement('style');
    style.textContent = `
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            z-index: 10000;
            justify-content: center;
            align-items: center;
            backdrop-filter: blur(8px);
            animation: fadeIn 0.3s ease;
        }

        .modal-overlay.active {
            display: flex;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes slideUp {
            from { transform: translateY(50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        .modal-content {
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            border: 2px solid #ff9500;
            border-radius: 16px;
            max-width: 600px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 0 50px rgba(255, 149, 0, 0.4);
            animation: slideUp 0.4s ease;
        }

        .modal-header {
            padding: 2rem;
            border-bottom: 1px solid rgba(255, 149, 0, 0.2);
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }

        .modal-icon {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5rem;
            flex-shrink: 0;
        }

        .modal-icon.success {
            background: linear-gradient(135deg, #08c45a, #00a650);
            box-shadow: 0 0 20px rgba(8, 196, 90, 0.4);
        }

        .modal-icon.warning {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            box-shadow: 0 0 20px rgba(231, 76, 60, 0.4);
        }

        .modal-header-text h2 {
            color: #fff;
            font-size: 1.8rem;
            margin: 0 0 0.3rem 0;
            font-weight: 700;
        }

        .modal-header-text small {
            color: #b0b0b0;
            font-size: 0.95rem;
        }

        .modal-body {
            padding: 2rem;
            color: #ddd;
            font-size: 1rem;
            line-height: 1.8;
        }

        .modal-footer {
            padding: 1.5rem 2rem;
            border-top: 1px solid rgba(255, 149, 0, 0.2);
            display: flex;
            justify-content: center;
        }

        .modal-btn-success,
        .modal-btn-primary {
            padding: 1rem 2rem;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.3s;
        }

        .modal-btn-success {
            background: linear-gradient(135deg, #08c45a, #00a650);
            color: #fff;
        }

        .modal-btn-success:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(8, 196, 90, 0.4);
        }

        .modal-btn-primary {
            background: linear-gradient(135deg, #ff9500, #ffa726);
            color: #000;
        }

        .modal-btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(255, 149, 0, 0.4);
        }

        @media (max-width: 768px) {
            .modal-content {
                width: 95%;
                max-height: 85vh;
            }

            .modal-header {
                padding: 1.5rem;
                flex-direction: column;
                text-align: center;
            }

            .modal-header-text h2 {
                font-size: 1.5rem;
            }

            .modal-body {
                padding: 1.5rem;
                font-size: 0.95rem;
            }

            .modal-footer {
                padding: 1rem 1.5rem;
            }

            .modal-btn-success,
            .modal-btn-primary {
                width: 100%;
                justify-content: center;
            }
        }
    `;
    document.head.appendChild(style);
}

function criarInterfacePassoAPassoCompleta() {
    const colunaInputs = document.querySelector('.ods-simulador__inputs');
    if (!colunaInputs) return;

    // esconder inputs antigos
    colunaInputs.querySelectorAll('.ods-simulador__grupo').forEach(g => g.style.display = 'none');

    if (document.getElementById('simuladorPassoContainerFull')) return;

    const container = document.createElement('div');
    container.id = 'simuladorPassoContainerFull';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.gap = '14px';

    // barra de progresso
    const progresso = document.createElement('div');
    progresso.style.height = '10px';
    progresso.style.background = '#e9e9e9';
    progresso.style.borderRadius = '8px';
    progresso.style.overflow = 'hidden';
    progresso.innerHTML = `<div id="simProgressoBarFull" style="width:0%;height:100%;background:linear-gradient(90deg,#4CAF50,#66BB6A);"></div>`;
    container.appendChild(progresso);

    const passoArea = document.createElement('div');
    passoArea.id = 'simPassoAreaFull';
    container.appendChild(passoArea);

    const nav = document.createElement('div');
    nav.style.display = 'flex';
    nav.style.gap = '8px';

    const btnBack = document.createElement('button');
    btnBack.id = 'simFullBtnBack';
    btnBack.textContent = 'Voltar';
    btnBack.disabled = true;
    btnBack.style.flex = '1';
    btnBack.style.padding = '12px';
    btnBack.style.borderRadius = '8px';
    btnBack.style.background = '#bdbdbd';
    btnBack.style.border = 'none';
    btnBack.style.color = '#fff';

    const btnNext = document.createElement('button');
    btnNext.id = 'simFullBtnNext';
    btnNext.textContent = 'Próximo';
    btnNext.style.flex = '1';
    btnNext.style.padding = '12px';
    btnNext.style.borderRadius = '8px';
    btnNext.style.background = '#2e7d32';
    btnNext.style.border = 'none';
    btnNext.style.color = '#fff';

    nav.appendChild(btnBack);
    nav.appendChild(btnNext);
    container.appendChild(nav);

    colunaInputs.insertBefore(container, colunaInputs.firstChild);

    window._simuladorFull = {
        step: 1,
        placa: 5,
        consumoBase: 200,
        pessoas: 2,
        ar: 'nao',
        aparelhosNoite: 'alguns',
        contaValor: 0
    };

    btnBack.addEventListener('click', () => {
        if (window._simuladorFull.step > 1) {
            window._simuladorFull.step--;
            renderizarPassoFull();
        }
    });

    btnNext.addEventListener('click', () => {
        if (window._simuladorFull.step < 5) {
            window._simuladorFull.step++;
            renderizarPassoFull();
        } else {
            window._simuladorFull.step = 1;
            renderizarPassoFull();
        }
    });

    renderizarPassoFull();
}

function renderizarPassoFull() {
    const area = document.getElementById('simPassoAreaFull');
    const bar = document.getElementById('simProgressoBarFull');
    const s = window._simuladorFull;

    area.innerHTML = '';
    bar.style.width = ((s.step - 1) / 4) * 100 + '%';

    const btnBack = document.getElementById('simFullBtnBack');
    const btnNext = document.getElementById('simFullBtnNext');

    btnBack.disabled = s.step === 1;
    btnNext.textContent = s.step === 5 ? "Refazer" : "Próximo";

    /* ================= PASSO 1 – MODELO 2 (Cartões limpos) ================= */
    if (s.step === 1) {
        area.innerHTML = `
            <h3>1) Escolha a quantidade de placas do seu sistema</h3>
            <p>Quanto mais placas, mais energia você gera.</p>
        `;

        const op = [
            { val: 3, text: "Poucas placas – 3 kW", color: "#FFB74D" },
            { val: 5, text: "Várias placas – 5 kW", color: "#FFA726" },
            { val: 10, text: "Muitas placas – 10 kW", color: "#FB8C00" }
        ];

        const box = criarColuna();
        op.forEach(o => {
            const card = criarCard(o.text, s.placa === o.val, o.color);
            card.onclick = () => { s.placa = o.val; renderizarPassoFull(); atualizar(); };
            box.appendChild(card);
        });

        area.appendChild(box);
    }

    /* ================= PASSO 2 ================= */
    if (s.step === 2) {
        area.innerHTML = `
            <h3>2) Seu consumo mensal aproximado</h3>
            <p>Escolha a opção que mais representa sua casa.</p>
        `;

        const op = [
            { val: 100, text: "Conta baixa (≈100 kWh)", color: "#FFB74D" },
            { val: 200, text: "Conta média (≈200 kWh)", color: "#FFA726" },
            { val: 350, text: "Conta alta (≈350 kWh)", color: "#FB8C00" }
        ];

        const box = criarColuna();
        op.forEach(o => {
            const card = criarCard(o.text, s.consumoBase === o.val, o.color);
            card.onclick = () => { s.consumoBase = o.val; renderizarPassoFull(); atualizar(); };
            box.appendChild(card);
        });

        area.appendChild(box);
    }

    /* ================= PASSO 3 ================= */
    if (s.step === 3) {
        area.innerHTML = `
            <h3>3) Quantas pessoas moram na casa?</h3>
            <p>Mais pessoas = maior consumo.</p>
        `;

        const opPessoas = [
            { val: 1, text: "1 pessoa", color: "#FFB74D" },
            { val: 2, text: "2–3 pessoas", color: "#FFA726" },
            { val: 4, text: "4+ pessoas", color: "#FB8C00" }
        ];

        const box = criarColuna();
        opPessoas.forEach(o => {
            const card = criarCard(o.text, s.pessoas === o.val, o.color);
            card.onclick = () => { s.pessoas = o.val; renderizarPassoFull(); atualizar(); };
            box.appendChild(card);
        });

        area.appendChild(box);

        /* Ar-condicionado */
        const h2 = document.createElement('h3');
        h2.textContent = "Você usa ar-condicionado?";
        h2.style.marginTop = "12px";
        area.appendChild(h2);

        const opAr = [
            { val: 'nao', text: "Não uso", color: "#FFB74D" },
            { val: 'as_vezes', text: "Uso às vezes", color: "#FFA726" },
            { val: 'sempre', text: "Uso todo dia", color: "#FB8C00" }
        ];

        const box2 = criarColuna();
        opAr.forEach(o => {
            const card = criarCard(o.text, s.ar === o.val, o.color);
            card.onclick = () => { s.ar = o.val; renderizarPassoFull(); atualizar(); };
            box2.appendChild(card);
        });

        area.appendChild(box2);
    }

    /* ================= PASSO 4 ================= */
    if (s.step === 4) {
        area.innerHTML = `
            <h3>4) Quantos aparelhos ficam ligados à noite?</h3>
            <p>Noite costuma ter alto consumo por iluminação e TV.</p>
        `;

        const op = [
            { val: 'pouco', text: "Quase nenhum", color: "#FFB74D" },
            { val: 'alguns', text: "Alguns aparelhos", color: "#FFA726" },
            { val: 'muitos', text: "Muitos aparelhos", color: "#FB8C00" }
        ];

        const box = criarColuna();
        op.forEach(o => {
            const card = criarCard(o.text, s.aparelhosNoite === o.val, o.color);
            card.onclick = () => { s.aparelhosNoite = o.val; renderizarPassoFull(); atualizar(); };
            box.appendChild(card);
        });

        area.appendChild(box);
    }

    /* ================= PASSO 5 – RESULTADO FINAL ================= */
    if (s.step === 5) {
        area.innerHTML = `
            <h3>5) Quanto você paga na conta de luz (R$)?</h3>
            <p>Se não souber, deixe em branco.</p>
        `;

        const wrap = document.createElement('div');
        wrap.style.display = 'flex';
        wrap.style.gap = '10px';

        const input = document.createElement('input');
        input.type = "number";
        input.placeholder = "Ex: 150";
        input.value = s.contaValor || "";
        input.style.padding = '10px';
        input.style.flex = '1';
        input.style.borderRadius = '8px';
        input.style.border = '1px solid #ccc';

        const btn = document.createElement('button');
        btn.textContent = "Calcular";
        btn.style.padding = '10px 14px';
        btn.style.background = '#1976D2';
        btn.style.color = 'white';
        btn.style.border = 'none';
        btn.style.borderRadius = '8px';

        btn.onclick = () => {
            const v = parseFloat(input.value);
            s.contaValor = isNaN(v) ? 0 : v;
            renderizarPassoFull();
            atualizar();
        };

        wrap.appendChild(input);
        wrap.appendChild(btn);
        area.appendChild(wrap);

        const result = document.createElement('div');
        result.id = "resultadoPasso5Full";
        result.style.marginTop = "12px";
        area.appendChild(result);

        mostrarResultadoFinal();
    }

    atualizar();
}

function criarColuna() {
    const c = document.createElement('div');
    c.style.display = 'flex';
    c.style.flexDirection = 'column';
    c.style.gap = '10px';
    return c;
}

function criarCard(texto, selecionado, cor) {
    const card = document.createElement('div');
    card.textContent = texto;
    card.style.padding = '14px';
    card.style.borderRadius = '10px';
    card.style.cursor = 'pointer';
    card.style.fontWeight = '700';
    card.style.transition = '0.2s';
    card.style.boxShadow = '0 3px 12px rgba(0,0,0,0.08)';

    if (selecionado) {
        card.style.background = cor || '#4CAF50';
        card.style.color = '#fff';
        card.style.border = '2px solid rgba(0,0,0,0.06)';
    } else {
        card.style.background = '#ffffff';
        card.style.color = '#1f2937';
        card.style.border = '1px solid #e6edf3';
    }

    card.onmouseenter = () => {
        card.style.transform = 'translateY(-3px)';
        card.style.boxShadow = '0 8px 20px rgba(0,0,0,0.08)';
    };
    card.onmouseleave = () => {
        card.style.transform = 'translateY(0)';
        card.style.boxShadow = '0 3px 12px rgba(0,0,0,0.08)';
    };

    return card;
}

/* ================= CÁLCULOS ================= */

function calcularConsumoEstimado() {
    const s = window._simuladorFull;
    let c = s.consumoBase;

    if (s.pessoas === 1) c *= 0.8;
    else if (s.pessoas === 4) c *= 1.25;

    if (s.ar === 'as_vezes') c *= 1.15;
    else if (s.ar === 'sempre') c *= 1.7;

    if (s.aparelhosNoite === 'pouco') c *= 0.9;
    else if (s.aparelhosNoite === 'muitos') c *= 1.2;

    if (s.contaValor && s.contaValor > 0) {
        const contaImplica = s.contaValor / TARIFA;
        c = c * 0.6 + contaImplica * 0.4;
    }

    return Math.round(c);
}

function mostrarResultadoFinal() {
  const s = window._simuladorFull;
  const consumoEst = calcularConsumoEstimado();
  const geracao = GERACAO_DIA[s.placa] * 30;
  const diferenca = geracao - consumoEst;
  const economiaAnual = Math.max(0, Math.min(geracao, consumoEst)) * TARIFA * 12;

  const wrap = document.getElementById('resultadoPasso5Full');
  if (!wrap) return;

  wrap.innerHTML = '';

  const resultados = document.createElement('div');
  resultados.style.display = 'flex';
  resultados.style.flexDirection = 'column';
  resultados.style.gap = '1rem';

  resultados.innerHTML = `
    <div style="padding:1.2rem;border-radius:10px;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.1);color:#ddd;font-size:0.95rem;">
      <strong>Consumo estimado:</strong> ${consumoEst} kWh/mês
    </div>
    <div style="padding:1.2rem;border-radius:10px;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.1);color:#ddd;font-size:0.95rem;">
      <strong>Geração:</strong> ${geracao} kWh/mês
    </div>
    <div style="padding:1.2rem;border-radius:10px;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.1);color:#ddd;font-size:0.95rem;">
      <strong>Sobra/Falta:</strong> ${diferenca >= 0 ? "Sobra " + diferenca : "Falta " + Math.abs(diferenca)} kWh
    </div>
    <div style="padding:1.2rem;border-radius:10px;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.1);color:#ddd;font-size:0.95rem;">
      <strong>Economia anual:</strong> R$ ${economiaAnual.toFixed(2).replace(".", ",")}
    </div>
  `;

  wrap.appendChild(resultados);

  const btnMostrarResultado = document.createElement('button');
  btnMostrarResultado.style.marginTop = '1rem';
  btnMostrarResultado.style.padding = '1rem';
  btnMostrarResultado.style.background = geracao > consumoEst ? '#08c45a' : '#f1c40f';
  btnMostrarResultado.style.color = '#000';
  btnMostrarResultado.style.border = 'none';
  btnMostrarResultado.style.borderRadius = '8px';
  btnMostrarResultado.style.fontWeight = '700';
  btnMostrarResultado.style.cursor = 'pointer';
  btnMostrarResultado.style.transition = 'all 0.3s';
  btnMostrarResultado.textContent = '📊 Ver Resultado Detalhado';

  btnMostrarResultado.addEventListener('mouseenter', () => {
    btnMostrarResultado.style.transform = 'translateY(-2px)';
    btnMostrarResultado.style.boxShadow = `0 8px 20px ${geracao > consumoEst ? 'rgba(8,196,90,0.4)' : 'rgba(241,196,15,0.4)'}`;
  });

  btnMostrarResultado.addEventListener('mouseleave', () => {
    btnMostrarResultado.style.transform = 'translateY(0)';
  });

  btnMostrarResultado.addEventListener('click', () => {
    if (geracao > consumoEst) {
      showSimuladorResultadoPositivo(diferenca, economiaAnual);
    } else {
      showSimuladorResultadoNegativo(Math.abs(diferenca), economiaAnual);
    }
  });

  wrap.appendChild(btnMostrarResultado);
}

function showSimuladorResultadoPositivo(diferenca, economia) {
  const s = window._simuladorFull;
  const consumoEst = calcularConsumoEstimado();
  const geracao = GERACAO_DIA[s.placa] * 30;
  const valorMensalEconomizado = (Math.min(geracao, consumoEst) * TARIFA);
  const percentualEconomia = consumoEst > 0 ? ((Math.min(geracao, consumoEst) / consumoEst) * 100) : 0;
  
  // ✅ CORREÇÃO: Cálculo dinâmico do CO₂
  const energiaAproveitada = Math.min(geracao, consumoEst);
  const co2Evitado = (energiaAproveitada * 0.356).toFixed(2);
  const arvoresEquivalentes = Math.round(parseFloat(co2Evitado) / 21);
  
  const modal = getOrCreateModal('modalSimuladorPositivo', `
    <div class="modal-overlay" id="modalSimuladorPositivo">
      <div class="modal-content" style="max-width:700px;">
        <div class="modal-header">
          <div class="modal-icon success">
            <i class="fas fa-check-circle"></i>
          </div>
          <div class="modal-header-text">
            <h2>🎉 Parabéns! Resultado Excelente!</h2>
            <small>Sua placa gera MAIS energia do que você consome</small>
          </div>
        </div>
        <div class="modal-body">
          <div style="background:linear-gradient(135deg, rgba(8,196,90,0.15), rgba(0,166,80,0.05));padding:1.5rem;border-radius:12px;border-left:4px solid #08c45a;margin-bottom:1.5rem;">
            <h3 style="color:#08c45a;margin:0 0 1rem 0;font-size:1.3rem;">📊 Resumo Detalhado</h3>
            
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1rem;">
              <div style="background:rgba(255,255,255,0.08);padding:1rem;border-radius:8px;">
                <div style="color:#b0b0b0;font-size:0.85rem;margin-bottom:0.3rem;">Geração Mensal</div>
                <div style="color:#fff;font-size:1.5rem;font-weight:700;">${geracao.toFixed(0)} kWh</div>
              </div>
              
              <div style="background:rgba(255,255,255,0.08);padding:1rem;border-radius:8px;">
                <div style="color:#b0b0b0;font-size:0.85rem;margin-bottom:0.3rem;">Seu Consumo</div>
                <div style="color:#fff;font-size:1.5rem;font-weight:700;">${consumoEst.toFixed(0)} kWh</div>
              </div>
            </div>

            <div style="background:rgba(8,196,90,0.2);padding:1.2rem;border-radius:10px;margin-bottom:1rem;text-align:center;">
              <div style="color:#08c45a;font-size:0.9rem;margin-bottom:0.5rem;">✨ EXCEDENTE DE ENERGIA</div>
              <div style="color:#08c45a;font-size:2.2rem;font-weight:800;">+${diferenca.toFixed(0)} kWh/mês</div>
              <div style="color:#b0b0b0;font-size:0.85rem;margin-top:0.5rem;">Energia disponível para doação ou créditos</div>
            </div>
          </div>

          <div style="background:rgba(255,255,255,0.05);padding:1.5rem;border-radius:12px;margin-bottom:1.5rem;">
            <h3 style="color:#ffa726;margin:0 0 1rem 0;font-size:1.2rem;">💰 Impacto Financeiro</h3>
            
            <div style="display:grid;gap:0.8rem;">
              <div style="display:flex;justify-content:space-between;align-items:center;padding:0.8rem;background:rgba(255,255,255,0.03);border-radius:6px;">
                <span style="color:#ddd;">Economia mensal:</span>
                <strong style="color:#08c45a;font-size:1.2rem;">R$ ${valorMensalEconomizado.toFixed(2).replace(".", ",")}</strong>
              </div>
              
              <div style="display:flex;justify-content:space-between;align-items:center;padding:0.8rem;background:rgba(255,255,255,0.03);border-radius:6px;">
                <span style="color:#ddd;">Economia anual:</span>
                <strong style="color:#08c45a;font-size:1.2rem;">R$ ${economia.toFixed(2).replace(".", ",")}</strong>
              </div>
              
              <div style="display:flex;justify-content:space-between;align-items:center;padding:0.8rem;background:rgba(255,255,255,0.03);border-radius:6px;">
                <span style="color:#ddd;">Redução na conta:</span>
                <strong style="color:#08c45a;font-size:1.2rem;">${percentualEconomia.toFixed(0)}%</strong>
              </div>
            </div>
          </div>

          <div style="background:rgba(76,175,80,0.1);padding:1.5rem;border-radius:12px;margin-bottom:1.5rem;">
            <h3 style="color:#4CAF50;margin:0 0 1rem 0;font-size:1.2rem;">🌱 Impacto Ambiental</h3>
            
            <div style="text-align:center;padding:1rem;">
              <div style="color:#4CAF50;font-size:2rem;font-weight:700;margin-bottom:0.5rem;">${co2Evitado} kg CO₂</div>
              <div style="color:#b0b0b0;font-size:0.9rem;">Evitados mensalmente na atmosfera</div>
              <div style="color:#b0b0b0;font-size:0.85rem;margin-top:0.8rem;font-style:italic;">
                Equivalente a plantar ${Math.round(parseFloat(co2Evitado) / 21)} árvores 🌳
              </div>
            </div>
          </div>

          <div style="background:rgba(255,152,0,0.1);padding:1.5rem;border-radius:12px;border-left:4px solid #ff9800;">
            <h3 style="color:#ffa726;margin:0 0 1rem 0;font-size:1.1rem;">💡 O que fazer com seu excedente?</h3>
            
            <div style="display:grid;gap:0.8rem;">
              <div style="padding:0.8rem;background:rgba(255,255,255,0.05);border-radius:6px;">
                <strong style="color:#08c45a;">✓ Doar para famílias carentes</strong>
                <div style="color:#b0b0b0;font-size:0.85rem;margin-top:0.3rem;">Transforme seu excedente em solidariedade</div>
              </div>
              
              <div style="padding:0.8rem;background:rgba(255,255,255,0.05);border-radius:6px;">
                <strong style="color:#08c45a;">✓ Acumular créditos de energia</strong>
                <div style="color:#b0b0b0;font-size:0.85rem;margin-top:0.3rem;">Use nos próximos meses ou anos</div>
              </div>
              
              <div style="padding:0.8rem;background:rgba(255,255,255,0.05);border-radius:6px;">
                <strong style="color:#08c45a;">✓ Compartilhar com outras unidades</strong>
                <div style="color:#b0b0b0;font-size:0.85rem;margin-top:0.3rem;">Se você possui outros imóveis</div>
              </div>
            </div>
          </div>

          <div style="background:linear-gradient(135deg, rgba(8,196,90,0.2), rgba(0,166,80,0.1));padding:1.5rem;border-radius:12px;margin-top:1.5rem;text-align:center;">
            <div style="font-size:1.5rem;margin-bottom:0.5rem;">💚</div>
            <strong style="color:#08c45a;font-size:1.1rem;display:block;margin-bottom:0.5rem;">
              Seu impacto pode ser ainda maior!
            </strong>
            <div style="color:#ddd;font-size:0.95rem;">
              Junte-se ao nosso programa de doação e ajude famílias que precisam de energia
            </div>
          </div>
        </div>
        <div class="modal-footer" style="padding:1.5rem 2rem;">
          <button class="modal-btn-success" onclick="window.location.href='/login.html'" style="width:100%;padding:1.2rem;font-size:1.1rem;">
            <i class="fas fa-heart"></i> Quero Doar Meu Excedente Agora!
          </button>
        </div>
      </div>
    </div>
  `);
  modal.classList.add('active');
}

function showSimuladorResultadoNegativo(deficit, economia) {
  const modal = getOrCreateModal('modalSimuladorNegativo', `
    <div class="modal-overlay" id="modalSimuladorNegativo">
      <div class="modal-content">
        <div class="modal-header">
          <div class="modal-icon warning">
            <i class="fas fa-exclamation-circle"></i>
          </div>
          <div class="modal-header-text">
            <h2>Atenção!</h2>
            <small>Sua casa usa MAIS energia</small>
          </div>
        </div>
        <div class="modal-body">
          <strong style="color:#e74c3c;">⚠ Sua casa usa MAIS energia do que sua placa solar gera.</strong>
          <br><br>
          Você tem um <strong>déficit de -${deficit.toFixed(0)} kWh/mês</strong>. Isso significa que você precisaria aumentar a capacidade de sua placa solar ou reduzir o consumo.
          <br><br>
          <em style="color:#b0b0b0;">Dica: Considere adicionar mais painéis solares ao seu sistema.</em>
        </div>
        <div class="modal-footer">
          <button class="modal-btn-primary" onclick="closeModalInterativo('modalSimuladorNegativo')">
            <i class="fas fa-redo"></i> Refazer Simulação
          </button>
        </div>
      </div>
    </div>
  `);
  modal.classList.add('active');
}

/* ================= ÁREA LATERAL (COLUNA DIREITA) ================= */

function atualizar() {
    if (!window._simuladorFull) return;

    const s = window._simuladorFull;

    const consumoEst = calcularConsumoEstimado();
    const geracao = GERACAO_DIA[s.placa] * 30;

    const economiaAnual = Math.max(0, Math.min(geracao, consumoEst)) * TARIFA * 12;

    const diferenca = geracao - consumoEst;

    set("energiaGerada", geracao + " kWh/mês");
    set("consumoMensal", consumoEst + " kWh/mês");
    set("diferenca", (diferenca >= 0 ? '+' : '') + diferenca + " kWh/mês");
    set("economiaAnual", "R$ " + economiaAnual.toFixed(2).replace(".", ","));
}

function set(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function getOrCreateModal(modalId, html) {
    let modal = document.getElementById(modalId);
    const parent = document.body;

    // If modal does not exist, create it
    if (!modal) {
        parent.insertAdjacentHTML('beforeend', html || '');
        modal = document.getElementById(modalId);
    } else if (html) {
        // If modal exists but new HTML provided, replace it so dynamic values are updated
        modal.remove();
        parent.insertAdjacentHTML('beforeend', html);
        modal = document.getElementById(modalId);
    }

    // attach click-to-close listener (safe to attach even if already attached because
    // we remove and recreate the node when updating)
    if (modal && !modal.__modalClickHandlerAttached) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
        // mark as attached to avoid duplicate handlers if node persists
        modal.__modalClickHandlerAttached = true;
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
document.addEventListener('DOMContentLoaded', function() {
    const simuladorForm = document.getElementById('simulador-solar');
    const modalResultado = document.getElementById('modal-resultado');
    const btnFecharModal = document.querySelector('.btn-fechar-modal');
    const btnDoar = document.getElementById('btn-doar-agora');

    // Variáveis para armazenar o cálculo atual
    let calculoAtual = null;

    simuladorForm.addEventListener('submit', function(e) {
        e.preventDefault();
        calcularSimulacao();
    });

    btnFecharModal?.addEventListener('click', fecharModal);
    modalResultado?.addEventListener('click', function(e) {
        if (e.target === modalResultado) fecharModal();
    });

    btnDoar?.addEventListener('click', function() {
        window.location.href = '/login.html';
    });

    function calcularSimulacao() {
        // Captura valores ATUAIS do formulário
        const valorConta = parseFloat(document.getElementById('valor-conta').value);
        const numMoradores = parseInt(document.getElementById('num-moradores').value);
        const kwh = parseFloat(document.getElementById('consumo-kwh').value);

        if (!valorConta || !numMoradores || !kwh) {
            alert('Preencha todos os campos!');
            return;
        }

        // CÁLCULO REAL
        const tarifaMedia = valorConta / kwh; // R$ por kWh
        const geracaoMensal = kwh * 1.2; // 20% a mais de geração
        const consumoMensal = kwh;
        
        // Calcula excedente real
        const excedente = geracaoMensal - consumoMensal;
        const economiaAnual = valorConta * 12;

        // Armazena cálculo
        calculoAtual = {
            valorConta,
            numMoradores,
            kwh,
            geracaoMensal,
            consumoMensal,
            excedente,
            economiaAnual,
            tarifaMedia
        };

        exibirResultado(calculoAtual);
    }

    function exibirResultado(dados) {
        const modalContent = modalResultado.querySelector('.modal-resultado-content');
        
        if (dados.excedente > 0) {
            // RESULTADO POSITIVO - Gera mais que consome
            modalContent.innerHTML = `
                <div class="resultado-header positivo">
                    <div class="resultado-icone">
                        <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
                            <circle cx="30" cy="30" r="28" fill="#10b981" stroke="#059669" stroke-width="2"/>
                            <path d="M20 30L26 36L40 22" stroke="white" stroke-width="4" stroke-linecap="round"/>
                        </svg>
                    </div>
                    <h2>Ótimo resultado!</h2>
                    <p>Sua placa gera MAIS energia</p>
                </div>

                <div class="resultado-detalhes positivo">
                    <p class="destaque">✅ Sua placa solar gera MAIS energia do que você usa.</p>
                    
                    <div class="info-item">
                        <span class="icone">🏭</span>
                        <strong>Geração mensal:</strong> ${dados.geracaoMensal.toFixed(0)} kWh
                    </div>
                    
                    <div class="info-item">
                        <span class="icone">🏠</span>
                        <strong>Seu consumo:</strong> ${dados.consumoMensal.toFixed(0)} kWh
                    </div>
                    
                    <div class="info-item destaque-verde">
                        <span class="icone">💡</span>
                        <strong>Excedente:</strong> +${dados.excedente.toFixed(0)} kWh/mês
                    </div>
                    
                    <div class="info-item">
                        <span class="icone">💰</span>
                        <strong>Economia anual:</strong> R$ ${dados.economiaAnual.toFixed(2)}
                    </div>

                    <div class="acoes-positivas">
                        <p>Com esse excedente, você pode:</p>
                        <ul>
                            <li>Doar para famílias carentes através da nossa plataforma</li>
                            <li>Acumular créditos de energia</li>
                            <li>Reduzir ainda mais sua conta de luz</li>
                        </ul>
                    </div>

                    <p class="cta-texto">
                        💚 <em>Considere se juntar ao nosso programa de doação e ajude famílias que precisam de energia!</em>
                    </p>
                </div>

                <button id="btn-doar-agora" class="btn-doar">
                    ❤️ Quero Doar Agora!
                </button>
            `;
        } else {
            // RESULTADO NEGATIVO - Consome mais que gera
            const deficit = Math.abs(dados.excedente);
            
            modalContent.innerHTML = `
                <div class="resultado-header negativo">
                    <div class="resultado-icone">
                        <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
                            <circle cx="30" cy="30" r="28" fill="#ef4444" stroke="#dc2626" stroke-width="2"/>
                            <path d="M30 20V35M30 42V42.5" stroke="white" stroke-width="4" stroke-linecap="round"/>
                        </svg>
                    </div>
                    <h2>Atenção!</h2>
                    <p>Sua casa usa MAIS energia</p>
                </div>

                <div class="resultado-detalhes negativo">
                    <p class="destaque aviso">⚠️ Sua casa usa MAIS energia do que sua placa solar gera.</p>
                    
                    <div class="info-item deficit">
                        <strong>Você tem um déficit de ${deficit.toFixed(0)} kWh/mês.</strong>
                        <p>Isso significa que você precisaria aumentar a capacidade da sua placa solar ou reduzir o consumo.</p>
                    </div>

                    <div class="dica">
                        <p><em>Dica: Considere adicionar mais painéis solares ao seu sistema.</em></p>
                    </div>
                </div>

                <button class="btn-refazer" onclick="document.getElementById('modal-resultado').style.display='none'">
                    🔄 Refazer Simulação
                </button>
            `;
        }

        // Reanexa event listener no botão doar
        const btnDoarNovo = document.getElementById('btn-doar-agora');
        if (btnDoarNovo) {
            btnDoarNovo.addEventListener('click', function() {
                window.location.href = '/login.html';
            });
        }

        modalResultado.style.display = 'flex';
    }

    function fecharModal() {
        modalResultado.style.display = 'none';
        simuladorForm.reset();
        calculoAtual = null;
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const simuladorForm = document.getElementById('simulador-solar');
    const modalResultado = document.getElementById('modal-resultado');
    const btnFecharModal = document.querySelector('.btn-fechar-modal');
    const btnDoar = document.getElementById('btn-doar-agora');

    // Variáveis para armazenar o cálculo atual
    let calculoAtual = null;

    simuladorForm.addEventListener('submit', function(e) {
        e.preventDefault();
        calcularSimulacao();
    });

    btnFecharModal?.addEventListener('click', fecharModal);
    modalResultado?.addEventListener('click', function(e) {
        if (e.target === modalResultado) fecharModal();
    });

    btnDoar?.addEventListener('click', function() {
        window.location.href = '/login.html';
    });

    function calcularSimulacao() {
        // Captura valores ATUAIS do formulário
        const valorConta = parseFloat(document.getElementById('valor-conta').value);
        const numMoradores = parseInt(document.getElementById('num-moradores').value);
        const kwh = parseFloat(document.getElementById('consumo-kwh').value);

        if (!valorConta || !numMoradores || !kwh) {
            alert('Preencha todos os campos!');
            return;
        }

        // CÁLCULO REAL
        const tarifaMedia = valorConta / kwh; // R$ por kWh
        const geracaoMensal = kwh * 1.2; // 20% a mais de geração
        const consumoMensal = kwh;
        
        // Calcula excedente real
        const excedente = geracaoMensal - consumoMensal;
        const economiaAnual = valorConta * 12;

        // Armazena cálculo
        calculoAtual = {
            valorConta,
            numMoradores,
            kwh,
            geracaoMensal,
            consumoMensal,
            excedente,
            economiaAnual,
            tarifaMedia
        };

        exibirResultado(calculoAtual);
    }

    function exibirResultado(dados) {
        const modalContent = modalResultado.querySelector('.modal-resultado-content');
        
        if (dados.excedente > 0) {
            // RESULTADO POSITIVO - Gera mais que consome
            modalContent.innerHTML = `
                <div class="resultado-header positivo">
                    <div class="resultado-icone">
                        <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
                            <circle cx="30" cy="30" r="28" fill="#10b981" stroke="#059669" stroke-width="2"/>
                            <path d="M20 30L26 36L40 22" stroke="white" stroke-width="4" stroke-linecap="round"/>
                        </svg>
                    </div>
                    <h2>Ótimo resultado!</h2>
                    <p>Sua placa gera MAIS energia</p>
                </div>

                <div class="resultado-detalhes positivo">
                    <p class="destaque">✅ Sua placa solar gera MAIS energia do que você usa.</p>
                    
                    <div class="info-item">
                        <span class="icone">🏭</span>
                        <strong>Geração mensal:</strong> ${dados.geracaoMensal.toFixed(0)} kWh
                    </div>
                    
                    <div class="info-item">
                        <span class="icone">🏠</span>
                        <strong>Seu consumo:</strong> ${dados.consumoMensal.toFixed(0)} kWh
                    </div>
                    
                    <div class="info-item destaque-verde">
                        <span class="icone">💡</span>
                        <strong>Excedente:</strong> +${dados.excedente.toFixed(0)} kWh/mês
                    </div>
                    
                    <div class="info-item">
                        <span class="icone">💰</span>
                        <strong>Economia anual:</strong> R$ ${dados.economiaAnual.toFixed(2)}
                    </div>

                    <div class="acoes-positivas">
                        <p>Com esse excedente, você pode:</p>
                        <ul>
                            <li>Doar para famílias carentes através da nossa plataforma</li>
                            <li>Acumular créditos de energia</li>
                            <li>Reduzir ainda mais sua conta de luz</li>
                        </ul>
                    </div>

                    <p class="cta-texto">
                        💚 <em>Considere se juntar ao nosso programa de doação e ajude famílias que precisam de energia!</em>
                    </p>
                </div>

                <button id="btn-doar-agora" class="btn-doar">
                    ❤️ Quero Doar Agora!
                </button>
            `;
        } else {
            // RESULTADO NEGATIVO - Consome mais que gera
            const deficit = Math.abs(dados.excedente);
            
            modalContent.innerHTML = `
                <div class="resultado-header negativo">
                    <div class="resultado-icone">
                        <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
                            <circle cx="30" cy="30" r="28" fill="#ef4444" stroke="#dc2626" stroke-width="2"/>
                            <path d="M30 20V35M30 42V42.5" stroke="white" stroke-width="4" stroke-linecap="round"/>
                        </svg>
                    </div>
                    <h2>Atenção!</h2>
                    <p>Sua casa usa MAIS energia</p>
                </div>

                <div class="resultado-detalhes negativo">
                    <p class="destaque aviso">⚠️ Sua casa usa MAIS energia do que sua placa solar gera.</p>
                    
                    <div class="info-item deficit">
                        <strong>Você tem um déficit de ${deficit.toFixed(0)} kWh/mês.</strong>
                        <p>Isso significa que você precisaria aumentar a capacidade da sua placa solar ou reduzir o consumo.</p>
                    </div>

                    <div class="dica">
                        <p><em>Dica: Considere adicionar mais painéis solares ao seu sistema.</em></p>
                    </div>
                </div>

                <button class="btn-refazer" onclick="document.getElementById('modal-resultado').style.display='none'">
                    🔄 Refazer Simulação
                </button>
            `;
        }

        // Reanexa event listener no botão doar
        const btnDoarNovo = document.getElementById('btn-doar-agora');
        if (btnDoarNovo) {
            btnDoarNovo.addEventListener('click', function() {
                window.location.href = '/login.html';
            });
        }

        modalResultado.style.display = 'flex';
    }

    function fecharModal() {
        modalResultado.style.display = 'none';
        simuladorForm.reset();
        calculoAtual = null;
    }
});