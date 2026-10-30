# Registrasi dan login — tahap logic

Modul memakai User, validasi password, hashing, dan session bawaan Django. Belum mengganti model User sehingga tidak mengganggu migrasi modul kelompok lainnya.

## Menjalankan

Salin `.env.example` menjadi `.env` (berisi `PRODUCTION=False`, sehingga lokal memakai SQLite). Instal requirements, jalankan `python manage.py migrate`, kemudian `python manage.py runserver`.

- `/register/`: username, email wajib, password, dan konfirmasi password. Berhasil membuat akun lalu mengarahkan ke halaman konfirmasi dan tautan login.
- `/login/`: login menggunakan **username**, bukan email. Setelah berhasil, kembali ke beranda atau tujuan `next` yang aman pada host yang sama.
- `/logout/`: POST dengan CSRF; mengakhiri session dan kembali ke login. GET tidak mengubah session.

Username mengikuti aturan dan keunikan bawaan Django. Email belum diverifikasi dan belum diperlakukan sebagai identitas unik. Akun baru tidak memiliki izin staff/superuser atau keanggotaan EO; formulir tidak menerima pilihan role admin. Group `EO` disediakan oleh migration Event Management dan ditetapkan oleh admin. EO dapat membuat serta mengubah/menghapus acara miliknya tanpa `is_staff`. Superuser dapat langsung mengelola semua acara tanpa Group `EO`. Food Waste Management tetap dibatasi untuk staff, terpisah dari EO. Lihat [panduan Event Management](event-management.md) untuk penetapan EO dan pengujian akses.

Formulir memakai desain responsif hijau–krem, tombol Google, pesan validasi, dan tombol tampilkan password. Proteksi brute-force/rate limiting dan pemulihan password belum diimplementasikan. Sebelum aplikasi dipakai publik, tambahkan pembatasan percobaan login.

## Profil dan direktori pengguna

Setiap User otomatis memiliki `Profile` (relasi satu-satu) yang dibuat oleh signal saat akun baru tersimpan; akun lama diberi profil melalui migration `0002_backfill_profiles`. Profil berisi nama tampilan, kota, bio, nomor HP, dan ID LINE.

- `/profil/`: halaman profil milik pengguna yang login, berisi formulir edit dan tautan hapus akun.
- `/profil/edit/`: POST; menyimpan perubahan profil. Halaman profil mengirimkannya lewat AJAX dan menampilkan pesan validasi per kolom tanpa memuat ulang halaman. Tanpa JavaScript, formulir tetap berfungsi dengan redirect biasa.
- `/profil/hapus/`: konfirmasi hapus akun dengan mengetik ulang username. Akun superuser ditolak, begitu pula akun yang masih memiliki acara. Setelah berhasil, session diakhiri.
- `/pengguna/`: direktori pengguna aktif dengan pencarian nama/username (`q`), filter kota (`kota`), dan 12 pengguna per halaman.
- `/pengguna/<username>/`: profil publik seorang pengguna.
- `/api/profil/`, `/api/pengguna/`, `/api/pengguna/<username>/`: data yang sama dalam format JSON.

Nomor HP dan ID LINE hanya ditampilkan kepada pengguna yang sudah login, baik di halaman HTML maupun di JSON. `/register/` juga mengembalikan JSON jika permintaan memakai header `Accept: application/json`.

## Deployment

Untuk PWS, isi Environs berdasarkan `.env.prod.example`: `PRODUCTION=True`, `SECRET_KEY` acak yang tetap, kredensial database ITF, `SCHEMA=tugas_kelompok`, serta `ALLOWED_HOSTS` dan `CSRF_TRUSTED_ORIGINS` yang sesuai. Saat start, `scripts/ensure_schema.py` membuat schema jika belum ada, lalu migration dijalankan otomatis.

## Pengujian

`python manage.py test authentication`

Menguji registrasi valid/tidak valid, password hashing, penolakan privilege dari input, duplikasi username, login gagal/nonaktif, session dan logout, redirect aman, CSRF, serta pembatasan admin Django. Untuk profil, diuji pembuatan profil otomatis, edit profil (HTML dan JSON), validasi nomor HP, hapus akun termasuk penolakan superuser dan akun yang masih memiliki acara, pencarian dan filter direktori, serta penyembunyian kontak dari pengunjung yang belum login.

## Masuk dengan Google

Integrasi memakai django-allauth 65.19.5 dengan OAuth authorization-code flow, state session, dan PKCE. Tombol tersedia pada login/register hanya jika kedua variabel `GOOGLE_CLIENT_ID` dan `GOOGLE_CLIENT_SECRET` terisi. Callback dan rute allauth tidak dimuat jika kredensial belum lengkap. Login password tetap tersedia.

### Konfigurasi Google Cloud

1. Buat/pilih project di Google Cloud Console, lalu konfigurasi Google Auth Platform/OAuth consent screen (nama aplikasi dan email kontak).
2. Buat OAuth Client ID berjenis **Web application**.
3. Daftarkan Authorized redirect URIs berikut secara persis, termasuk garis miring terakhir:
   - Lokal: `http://127.0.0.1:8000/accounts/google/login/callback/`
   - Jika memakai localhost: `http://localhost:8000/accounts/google/login/callback/`
   - PWS: `https://adinata-alaudin51-foodwaste.pws.cs.ui.ac.id/accounts/google/login/callback/`
4. Jika consent screen masih Testing, tambahkan akun penguji yang diperlukan pada daftar Test users.
5. Isi `GOOGLE_CLIENT_ID` dan `GOOGLE_CLIENT_SECRET` di `.env` lokal atau Environs PWS. Jangan commit atau mengirim Client Secret ke chat. Tidak perlu membuat SocialApp tambahan di Django admin karena kredensial berasal dari settings.
6. Instal requirements terbaru, jalankan `python manage.py migrate` untuk tabel allauth, kemudian restart aplikasi.
7. Buka `/login/`, tekan **Masuk dengan Google**, pilih akun dan selesaikan persetujuan. Uji juga logout dan login kembali.

Scope hanya profil dan email. Token Google tidak disimpan. Akun Google baru berstatus pengguna biasa, dengan password lokal tidak aktif. Jika email Google cocok dengan akun lokal yang belum terhubung, sistem meminta pengguna login memakai username/password; belum tersedia fitur pengaitan akun. Email Google yang tidak diverifikasi ditolak. Penolakan ini mencegah penggabungan otomatis dengan email lokal yang belum diverifikasi.

Pengujian callback memakai respons Google yang disimulasikan; pengujian langsung dengan Google membutuhkan kredensial OAuth valid. Konfigurasi produksi/proxy harus menghasilkan callback HTTPS yang persis sama dengan URI terdaftar.

Referensi: [Google provider django-allauth](https://docs.allauth.org/en/latest/socialaccount/providers/google.html).
