// Tarifa média de energia no Brasil (R$/kWh)
const TARIFA = 0.80;

// Geração diária por kW de placa solar (em kWh)
const GERACAO_DIA = { 3: 12, 5: 20, 10: 40 };

// Inicializa listeners de mudança nos inputs
function inicializar() {
    const placas = document.querySelectorAll('.placa-radio');
    const consumos = document.querySelectorAll('.consumo-radio');
    
    // Atualiza resultado quando muda a placa selecionada
    placas.forEach(p => p.addEventListener('change', atualizar));
    
    // Atualiza resultado quando muda o consumo selecionado
    consumos.forEach(c => c.addEventListener('change', atualizar));
    
    // Calcula valores iniciais
    atualizar();
}

// Executa o cálculo e atualiza os valores na tela
function atualizar() {
    const placa = document.querySelector('.placa-radio:checked');
    const consumo = document.querySelector('.consumo-radio:checked');
    
    if (!placa || !consumo) return;
    
    const placaVal = parseInt(placa.value);
    const consumoVal = parseInt(consumo.value);
    
    // Calcula energia gerada no mês (dias x geração diária)
    const energiaGerada = GERACAO_DIA[placaVal] * 30;
    
    // Diferença entre gerado e consumido
    const diferenca = energiaGerada - consumoVal;
    
    // Economia anual (energia gerada x tarifa x 12 meses)
    const economiaAnual = energiaGerada * TARIFA * 12;
    
    // Atualiza elementos HTML com novos valores
    document.getElementById('energiaGerada').textContent = energiaGerada;
    document.getElementById('consumoMensal').textContent = consumoVal;
    document.getElementById('diferenca').textContent = diferenca.toFixed(0) + ' kWh/mês';
    document.getElementById('economiaAnual').textContent = 'R$ ' + economiaAnual.toFixed(2).replace('.', ',');
}

// Executa quando a página carrega completamente
document.addEventListener('DOMContentLoaded', inicializar);