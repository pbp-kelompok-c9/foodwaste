// Interaktivitas modul profil: edit profil dan hapus akun lewat AJAX tanpa memuat ulang halaman.
// Token CSRF ikut terkirim karena FormData membawa input csrfmiddlewaretoken dari form.

const showErrors = (form, errors) => {
  form.querySelectorAll('[data-error-for]').forEach((el) => {
    const messages = (errors[el.dataset.errorFor] || []).map((error) => error.message);
    el.textContent = messages.join(' ');
    el.classList.toggle('tw-hidden', messages.length === 0);
  });
};

const submitForm = async (form) => {
  const response = await fetch(form.action, {
    method: 'POST',
    body: new FormData(form),
    headers: { Accept: 'application/json' },
    credentials: 'same-origin',
  });
  const data = await response.json().catch(() => ({}));
  return { ok: response.ok, data };
};

const profileForm = document.getElementById('profile-form');
if (profileForm) {
  const status = profileForm.querySelector('[data-form-status]');
  const button = profileForm.querySelector('button[type="submit"]');

  profileForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    button.disabled = true;
    status.textContent = 'Menyimpan…';
    try {
      const { ok, data } = await submitForm(profileForm);
      showErrors(profileForm, ok ? {} : data.errors || {});
      if (ok) {
        Object.entries(data.profile).forEach(([key, value]) => {
          document.querySelectorAll(`[data-profile="${key}"]`).forEach((el) => {
            el.textContent = value || '—';
          });
        });
        // Server merapikan penulisan kota; samakan isi input dengan hasil simpanan.
        profileForm.elements.city.value = data.profile.city;
      }
      status.textContent = ok ? data.message : 'Periksa kembali isian yang ditandai.';
    } catch {
      status.textContent = 'Gagal terhubung ke server. Coba lagi.';
    } finally {
      button.disabled = false;
    }
  });
}

const deleteForm = document.getElementById('delete-account-form');
if (deleteForm) {
  const button = deleteForm.querySelector('button[type="submit"]');

  deleteForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    button.disabled = true;
    try {
      const { ok, data } = await submitForm(deleteForm);
      if (ok) {
        window.location.assign(data.redirect);
        return;
      }
      showErrors(deleteForm, data.errors || {});
    } catch {
      showErrors(deleteForm, { __all__: [{ message: 'Gagal terhubung ke server. Coba lagi.' }] });
    }
    button.disabled = false;
  });
}
