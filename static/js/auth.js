document.querySelectorAll('[data-password]').forEach((button) => {
  const input = document.getElementById(button.dataset.password);
  if (!input) return;
  input.dataset.passwordInput = '';
  button.hidden = false;
  button.addEventListener('click', () => {
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    button.textContent = show ? 'Tutup' : 'Lihat';
    button.setAttribute('aria-pressed', String(show));
    button.setAttribute('aria-label', `${show ? 'Sembunyikan' : 'Tampilkan'} password`);
  });
});
