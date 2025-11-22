// Tarifa média de energia no Brasil (R$/kWh)
const TARIFA = 0.80;

// Geração diária por kW de placa solar (em kWh)
const GERACAO_DIA = { 3: 12, 5: 20, 10: 40 };

document.addEventListener('DOMContentLoaded', inicializar);

function inicializar() {
    criarInterfacePassoAPassoCompleta();
    atualizar(); // inicial
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

    /* ================= PASSO 1 — MODELO 2 (Cartões limpos) ================= */
    if (s.step === 1) {
        area.innerHTML = `
            <h3>1) Escolha a quantidade de placas do seu sistema</h3>
            <p>Quanto mais placas, mais energia você gera.</p>
        `;

        const op = [
            { val: 3, text: "Poucas placas — 3 kW", color: "#FFB74D" },   // Laranja claro
            { val: 5, text: "Várias placas — 5 kW", color: "#FFA726" },   // Laranja médio
            { val: 10, text: "Muitas placas — 10 kW", color: "#FB8C00" }  // Laranja forte
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
            { val: 'pouco', text: "Quase nenhum", color: "#FFB74D   " },
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

    /* ================= PASSO 5 — RESULTADO FINAL ================= */
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

    // melhorar legibilidade: texto escuro sobre fundo claro, texto claro sobre fundo escuro
    if (selecionado) {
        // background forte para seleção, texto branco
        card.style.background = cor || '#4CAF50';
        card.style.color = '#fff';
        card.style.border = '2px solid rgba(0,0,0,0.06)';
    } else {
        // fundo claro, texto escuro
        card.style.background = '#ffffff';
        card.style.color = '#1f2937'; // tom escuro e legível
        card.style.border = '1px solid #e6edf3';
    }

    // adicionar um indicador visual quando selecionado (sombra + escala)
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
    const wrap = document.getElementById('resultadoPasso5Full');

    if (!wrap) return;

    const consumoEst = calcularConsumoEstimado();
    const geracao = GERACAO_DIA[s.placa] * 30;
    const diferenca = geracao - consumoEst;

    const economiaAnual = Math.max(0, Math.min(geracao, consumoEst)) * TARIFA * 12;

    wrap.innerHTML = `
        <div style="padding:12px;border:1px solid #ddd;background:white;border-radius:8px;margin-bottom:8px;color: #000000ff">
            <strong>Consumo estimado:</strong> ${consumoEst} kWh/mês
        </div>
        <div style="padding:12px;border:1px solid #ddd;background:white;border-radius:8px;margin-bottom:8px;color: #000000ff">
            <strong>Geração:</strong> ${geracao} kWh/mês
        </div>
        <div style="padding:12px;border:1px solid #ddd;background:white;border-radius:8px;margin-bottom:8px;color: #000000ff">
            <strong>Sobra/Falta:</strong> ${diferenca >= 0 ? "Sobra " + diferenca : "Falta " + Math.abs(diferenca)} kWh
        </div>
        <div style="padding:12px;border:1px solid #ddd;background:white;border-radius:8px;margin-bottom:8px;color: #000000ff">
            <strong>Economia anual:</strong> R$ ${economiaAnual.toFixed(2).replace(".", ",")}
        </div>
    `;

    const resumo = document.createElement('div');
    resumo.style.padding = "12px";
    resumo.style.borderRadius = "8px";
    resumo.style.fontWeight = "700";

    if (geracao > consumoEst) {
        resumo.style.background = "#E8F5E9";
        resumo.style.color = "#000000ff";
        resumo.textContent = "Ótimo! Sua placa gera MAIS energia do que você usa.";
    } else if (geracao < consumoEst) {
        resumo.style.background = "#FFEBEE";
        resumo.style.color = "#000000ff";
        resumo.textContent = "Atenção! Sua casa usa MAIS energia do que sua placa gera.";
    } else {
        resumo.style.background = "#FFF3E0";
        resumo.style.color = "#000000ff";
        resumo.textContent = "Você está em equilíbrio perfeito!";
    }

    wrap.appendChild(resumo);
}

/* ================= ÁREA LATERAL (COLUNA DIREITA) ================= */

function atualizar() {
    if (!window._simuladorFull) return;

    const s = window._simuladorFull;

    const consumoEst = calcularConsumoEstimado();
    const geracao = GERACAO_DIA[s.placa] * 30;

    /* ====== THIM CORRIGIU (ECONOMIA ANUAL) ====== */
    const economiaAnual = Math.max(0, Math.min(geracao, consumoEst)) * TARIFA * 12;
    /* ====== THIM TERMINOU ====== */

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