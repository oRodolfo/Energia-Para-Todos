// Minimal modal alert component
(function (){
  function buildModal(opts) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';

    const dialog = document.createElement('div');
    dialog.className = 'modal-dialog modal-' + (opts.type || 'info');

    const header = document.createElement('div');
    header.className = 'modal-header';
    header.innerText = opts.title || '';

    const body = document.createElement('div');
    body.className = 'modal-body';
    if (typeof opts.message === 'string') {
      body.innerText = opts.message;
    } else if (opts.message instanceof Node) {
      body.appendChild(opts.message);
    }

    const footer = document.createElement('div');
    footer.className = 'modal-footer';

    const buttons = opts.buttons && opts.buttons.length ? opts.buttons : [{ label: 'OK', value: 'ok', class: 'btn-primary' }];

    buttons.forEach(b => {
      const btn = document.createElement('button');
      btn.className = 'modal-btn ' + (b.class || '');
      btn.innerText = b.label || 'OK';
      btn.addEventListener('click', () => {
        close(b.value);
      });
      footer.appendChild(btn);
    });

    dialog.appendChild(header);
    dialog.appendChild(body);
    dialog.appendChild(footer);
    overlay.appendChild(dialog);

    // Close helper
    function close(result) {
      document.body.removeChild(overlay);
      if (typeof opts.onClose === 'function') {
        try { opts.onClose(result); } catch (e) { console.error(e); }
      }
      resolvePromise(result);
    }

    // Make overlay dismissible by Escape
    function onKey(e) {
      if (e.key === 'Escape') {
        document.removeEventListener('keydown', onKey);
        close('esc');
      }
    }
    document.addEventListener('keydown', onKey);

    // small animation
    requestAnimationFrame(() => overlay.classList.add('visible'));

    return overlay;
  }

  let resolvePromise;
  window.showModalAlert = function(opts){
    return new Promise((resolve) => {
      resolvePromise = resolve;
      const modal = buildModal(opts || {});
      document.body.appendChild(modal);
    });
  };
})();
