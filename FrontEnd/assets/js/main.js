// Navegação suave para links âncora
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const targetId = this.getAttribute('href');
        const targetElement = document.querySelector(targetId);

        if (targetElement) {
            // O valor 80 é um offset para compensar a altura do header fixo
            const offsetPosition = targetElement.offsetTop - 80;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// Feather icons
feather.replace();

// Mobile menu logic
const mobileBtn = document.getElementById('mobile_btn');
const mobileMenu = document.getElementById('mobile_menu');

if (mobileBtn && mobileMenu) {
  mobileBtn.addEventListener('click', function(e){
    e.stopPropagation();
    const expanded = mobileMenu.classList.toggle('active');
    mobileMenu.setAttribute('aria-expanded', expanded);
    mobileBtn.setAttribute('aria-expanded', expanded);
    if(expanded) {
      mobileMenu.focus();
    }
  });

  // Fecha o menu ao clicar fora
  document.addEventListener('click', function(event){
    if (!mobileMenu.contains(event.target) && event.target !== mobileBtn) {
      mobileMenu.classList.remove('active');
      mobileMenu.setAttribute('aria-expanded', false);
      mobileBtn.setAttribute('aria-expanded', false);
    }
  });
}

// Máscara do telefone
const phoneInput = document.getElementById('phone');
if (phoneInput) {
  phoneInput.addEventListener('input', function(e) {
    let val = e.target.value.replace(/\D/g, '').slice(0, 11);
    let formatted = '';
    if(val.length > 0) formatted += '(' + val.substring(0,2);
    if(val.length >= 2) formatted += ') ' + val.substring(2,7);
    if(val.length >= 7) formatted += '-' + val.substring(7,11);
    e.target.value = formatted;
  });
}

// ===== FAQ accordion (index) =====
document.querySelectorAll('.faq__question').forEach(btn => {
  btn.addEventListener('click', () => {
    const item = btn.closest('.faq__item');
    const expanded = btn.getAttribute('aria-expanded') === 'true';
    if (item) {
      if (expanded) {
        item.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      } else {
        // fechar outros
        document.querySelectorAll('.faq__item.open').forEach(i => {
          i.classList.remove('open');
          const q = i.querySelector('.faq__question'); if (q) q.setAttribute('aria-expanded','false');
        });
        item.classList.add('open');
        btn.setAttribute('aria-expanded', 'true');
      }
    }
  });
});
