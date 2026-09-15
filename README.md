# FoodWaste

Proyek Tengah Semester PBP C — Kelompok C9.

## Deskripsi aplikasi

FoodWaste adalah aplikasi berbasis web untuk membantu pengelolaan makanan surplus pada acara melalui kerja sama dengan Event Organizer (EO). Peserta atau penyedia makanan dapat mengirim laporan berisi foto, lokasi, jumlah porsi, tenggat waktu best before yang diketahui pelapor, dan opsi penjemputan. EO menerima laporan melalui dashboard, menentukan tindak lanjut, dan mencatat proses pengambilan agar informasi makanan tidak tercecer dalam percakapan terpisah.

Alur yang direncanakan: laporan masuk → EO menerima atau menolak laporan → penanganan/penjemputan → selesai. Penerimaan laporan merupakan penerimaan untuk ditindaklanjuti, bukan sertifikasi kelayakan konsumsi. Kondisi makanan perlu diperiksa oleh petugas sebelum keputusan penanganan dibuat.

## Status Checkpoint 1

Code base Django 5.2 tersedia. Secara bawaan `CHECKPOINT_ONLY=True`: hanya halaman roket, tanpa akun/admin atau database persisten; SQLite sementara di memori digunakan agar langkah migrasi otomatis PWS tetap berjalan tanpa kredensial database. Untuk mulai mengembangkan fitur, gunakan `.env.example` (`CHECKPOINT_ONLY=False`). Halaman `/` menampilkan halaman roket bawaan Django, termasuk ketika `PRODUCTION=True`. Route sementara ini menggunakan halaman bawaan Django, sehingga teks bawaannya tentang DEBUG tidak mencerminkan konfigurasi server. Fitur aplikasi belum diimplementasikan.

## Anggota kelompok

| Nama | NPM | Program Studi | GitHub |
| --- | --- | --- | --- |
| Khansa Khairunnisa Haikal | 2506536465 | Sistem Informasi | — |
| Stefani Gwen Rolanda Tumbelaka | 2506594263 | Sistem Informasi | [stefanigwen14](https://github.com/stefanigwen14) |
| Muhammad Fatahillah Widodo | 2506623925 | Ilmu Komputer | — |
| Adinata Alaudin Pranaja | 2506656356 | Sistem Informasi | [adinatapranaja](https://github.com/adinatapranaja) |
| Angga Restha Rustyanto | 2506656444 | Ilmu Komputer | [AnggaRestha](https://github.com/AnggaRestha) |

## Rencana modul dan PIC

Usulan awal, belum merupakan pembagian final kelompok.

| Modul | Deskripsi | PIC |
| --- | --- | --- |
| Akun dan akses | Autentikasi serta pembatasan akses pelapor, EO, dan administrator | Belum ditentukan |
| Acara | Data acara, lokasi, dan pengelola EO | Belum ditentukan |
| Laporan makanan | Foto, jenis makanan, porsi, tenggat, lokasi, dan opsi penjemputan | Belum ditentukan |
| Tindak lanjut EO | Terima/tolak laporan, penugasan, dan perkembangan pengambilan | Belum ditentukan |
| Riwayat dan ringkasan | Riwayat laporan dan jumlah laporan per status | Belum ditentukan |

## Peran dan target pengguna

- Pelapor: peserta acara atau penyedia makanan yang melaporkan ketersediaan makanan.
- EO/panitia: mengelola acara, menerima laporan, dan mengoordinasikan penanganan.
- Administrator: mengelola akses EO dan data platform.

## Perbandingan aplikasi serupa

Belum diisi; perlu riset dan keputusan kelompok.

## Public API / mock API

Belum dipilih oleh kelompok. Halaman roket tidak memerlukan API eksternal.

## Deployment PWS

Belum dideploy. Tautan akan ditambahkan setelah proyek PWS berhasil berjalan.

## Desain Figma

Belum diisi oleh kelompok.

## Menjalankan lokal

Gunakan Python 3.10 atau lebih baru (pengembangan awal diuji dengan Python 3.13).

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py check
python manage.py runserver
```

Windows: gunakan `python -m venv .venv`, `.venv\Scripts\activate`, dan `copy .env.example .env`.

Buka http://127.0.0.1:8000/ untuk melihat roket Django. Hentikan server dengan Ctrl+C.

## Menyiapkan PWS

1. Proyek PWS bernama `foodwaste`. Checkpoint roket dapat dideploy tanpa mengisi database. Untuk mengaktifkan aplikasi lengkap nanti, set `CHECKPOINT_ONLY=False` dan ikuti konfigurasi berikut.
2. Isi Environs berdasarkan `.env.prod.example` menggunakan kredensial database ITF salah satu anggota. Gunakan schema `tugas_kelompok` untuk proyek kelompok.
3. Buat SECRET_KEY acak melalui `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` lalu simpan hanya di PWS Environs.
4. Isi ALLOWED_HOSTS dengan hostname deployment yang benar dan CSRF_TRUSTED_ORIGINS dengan URL HTTPS-nya.
5. Ikuti Project Command PWS untuk menambahkan remote. Jangan cantumkan password dalam README atau commit.
6. Push dengan `git push pws main:master`, periksa status Running dan buka View Project.
7. Tambahkan URL yang sudah diverifikasi ke bagian Deployment PWS di atas.

Konfigurasi PostgreSQL menggunakan schema `tugas_kelompok`; SQLite hanya dipakai lokal. `.env`, database lokal, dan virtual environment tidak diikutkan ke Git.

Referensi setup: https://pbp.cs.ui.ac.id/tutorial/tutorial-0.html dan https://pbp.cs.ui.ac.id/tutorial/tutorial-1.html
