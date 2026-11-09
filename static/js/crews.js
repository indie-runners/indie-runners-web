(function () {
  const input = document.getElementById('crew-invite-input');
  const btn = document.getElementById('crew-invite-copy');
  if (!input || !btn) return;

  function flash(text) {
    const original = btn.textContent;
    btn.textContent = text;
    setTimeout(() => { btn.textContent = original; }, 1500);
  }

  btn.addEventListener('click', async () => {
    const value = input.value;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(value);
        flash('Copied');
        return;
      }
    } catch (err) {
      // fall through to selection fallback
    }
    input.focus();
    input.select();
    try {
      document.execCommand('copy');
      flash('Copied');
    } catch (err) {
      flash('Press Ctrl+C');
    }
  });
})();
