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
