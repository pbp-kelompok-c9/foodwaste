# Registrasi dan login — tahap logic

Modul memakai User, validasi password, hashing, dan session bawaan Django. Belum mengganti model User sehingga tidak mengganggu migrasi modul kelompok lainnya.

## Menjalankan

Gunakan `.env.example` sebagai `.env` dengan `CHECKPOINT_ONLY=False`. Instal requirements, jalankan `python manage.py migrate`, kemudian `python manage.py runserver`.

- `/register/`: username, email wajib, password, dan konfirmasi password. Berhasil membuat akun lalu mengarahkan ke halaman konfirmasi dan tautan login.
- `/login/`: login menggunakan **username**, bukan email. Setelah berhasil, kembali ke beranda atau tujuan `next` yang aman pada host yang sama.
- `/logout/`: POST dengan CSRF; mengakhiri session dan kembali ke login. GET tidak mengubah session.

Username mengikuti aturan dan keunikan bawaan Django. Email belum diverifikasi dan belum diperlakukan sebagai identitas unik. Akun baru tidak memiliki izin staff/superuser; formulir tidak menerima pilihan role admin. Penetapan role EO dan pengelolaan profil belum termasuk tahap ini. Halaman Management belum dibatasi menjadi khusus EO karena kebijakan role tersebut belum diimplementasikan.

Formulir HTML hanya untuk mencoba logic, bukan desain final. Proteksi brute-force/rate limiting dan pemulihan password belum diimplementasikan. Sebelum aplikasi dipakai publik, tambahkan pembatasan percobaan login.

## Checkpoint dan deployment

`CHECKPOINT_ONLY=True` tetap menyediakan halaman roket tanpa auth dan database persisten. Rute aplikasi hanya dimuat saat mode checkpoint dimatikan. Untuk PWS dengan auth, siapkan database persisten, SECRET_KEY tetap, `PRODUCTION=True`, `CHECKPOINT_ONLY=False`, dan host/origin yang sesuai. Jangan mengaktifkan auth menggunakan database memori checkpoint.

## Pengujian

`CHECKPOINT_ONLY=False python manage.py test authentication`

Menguji registrasi valid/tidak valid, password hashing, penolakan privilege dari input, duplikasi username, login gagal/nonaktif, session dan logout, redirect aman, CSRF, serta pembatasan admin Django.

## Masuk dengan Google

Integrasi memakai django-allauth 65.19.5 dengan OAuth authorization-code flow, state session, dan PKCE. Tombol tersedia pada login/register hanya jika kedua variabel `GOOGLE_CLIENT_ID` dan `GOOGLE_CLIENT_SECRET` terisi. Callback dan rute allauth tidak dimuat jika kredensial belum lengkap atau mode checkpoint aktif. Login password tetap tersedia.

### Konfigurasi Google Cloud

1. Buat/pilih project di Google Cloud Console, lalu konfigurasi Google Auth Platform/OAuth consent screen (nama aplikasi dan email kontak).
2. Buat OAuth Client ID berjenis **Web application**.
3. Daftarkan Authorized redirect URIs berikut secara persis, termasuk garis miring terakhir:
   - Lokal: `http://127.0.0.1:8000/accounts/google/login/callback/`
   - Jika memakai localhost: `http://localhost:8000/accounts/google/login/callback/`
   - PWS: `https://adinata-alaudin51-foodwaste.pws.cs.ui.ac.id/accounts/google/login/callback/`
4. Jika consent screen masih Testing, tambahkan akun penguji yang diperlukan pada daftar Test users.
5. Isi `GOOGLE_CLIENT_ID` dan `GOOGLE_CLIENT_SECRET` di `.env` lokal atau Environs PWS. Jangan commit atau mengirim Client Secret ke chat. Tidak perlu membuat SocialApp tambahan di Django admin karena kredensial berasal dari settings.
6. Instal requirements terbaru, jalankan `python manage.py migrate` untuk tabel allauth, kemudian restart aplikasi. Mode aplikasi harus `CHECKPOINT_ONLY=False` dengan database persisten.
7. Buka `/login/`, tekan **Masuk dengan Google**, pilih akun dan selesaikan persetujuan. Uji juga logout dan login kembali.

Scope hanya profil dan email. Token Google tidak disimpan. Akun Google baru berstatus pengguna biasa, dengan password lokal tidak aktif. Jika email Google cocok dengan akun lokal yang belum terhubung, sistem meminta pengguna login memakai username/password; belum tersedia fitur pengaitan akun. Email Google yang tidak diverifikasi ditolak. Penolakan ini mencegah penggabungan otomatis dengan email lokal yang belum diverifikasi.

Pengujian callback memakai respons Google yang disimulasikan; pengujian langsung dengan Google membutuhkan kredensial OAuth valid. Konfigurasi produksi/proxy harus menghasilkan callback HTTPS yang persis sama dengan URI terdaftar.

Referensi: [Google provider django-allauth](https://docs.allauth.org/en/latest/socialaccount/providers/google.html).
