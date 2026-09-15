# FoodWaste

Proyek Tengah Semester PBP C — Kelompok C9.

## Deskripsi aplikasi

FoodWaste adalah aplikasi berbasis web yang dirancang untuk membantu mengurangi makanan terbuang pada acara melalui kerja sama dengan Event Organizer (EO). Aplikasi ini ditujukan untuk konser, acara keagamaan, kegiatan kampus, maupun acara berskala kecil. Makanan yang tidak termakan atau berlebih dapat dilaporkan oleh peserta agar penanganannya lebih teratur dan tidak langsung berakhir sebagai sampah.

Peserta yang sudah login dapat mengirim laporan ketersediaan makanan berisi foto, lokasi, jumlah porsi, tenggat waktu best before yang diketahui pelapor, dan opsi penjemputan. Admin dari pihak EO atau tim pengelola FoodWaste memeriksa laporan dan dapat menerima atau menolaknya apabila foto maupun informasi yang diberikan tidak sesuai ketentuan. Setelah laporan diterima dan kondisi makanan diperiksa, admin menentukan tindak lanjut berupa pengambilan, pengolahan, penjualan kembali, atau publikasi ulang untuk ditawarkan kepada peserta acara.

Nilai utama FoodWaste adalah menghubungkan laporan peserta dengan tindakan panitia dalam satu alur yang terpusat. Peserta mendapat cara praktis untuk melaporkan makanan, sementara EO dapat memantau ketersediaan dan proses penanganannya. Dengan demikian, aplikasi diharapkan membantu mengurangi makanan terbuang dan menjaga kebersihan lokasi setelah acara berakhir.

Alur yang direncanakan: peserta mengirim laporan → admin menerima atau menolak laporan → pemeriksaan dan penjemputan → admin menentukan penanganan atau menawarkan kembali makanan → selesai. Penerimaan laporan merupakan penerimaan untuk ditindaklanjuti, bukan sertifikasi kelayakan konsumsi. Kondisi makanan perlu diperiksa oleh petugas sebelum keputusan penanganan dibuat.

## Status Checkpoint 1

Code base Django 5.2 tersedia. Secara bawaan `CHECKPOINT_ONLY=True`: hanya halaman roket, tanpa akun/admin atau database persisten; SQLite sementara di memori digunakan agar langkah migrasi otomatis PWS tetap berjalan tanpa kredensial database. Untuk mulai mengembangkan fitur, gunakan `.env.example` (`CHECKPOINT_ONLY=False`). Halaman `/` menampilkan halaman roket bawaan Django, termasuk ketika `PRODUCTION=True`. Route sementara ini menggunakan halaman bawaan Django, sehingga teks bawaannya tentang DEBUG tidak mencerminkan konfigurasi server. Fitur aplikasi belum diimplementasikan.

## Anggota kelompok

| Nama | NPM | Program Studi | GitHub |
| --- | --- | --- | --- |
| Khansa Khairunnisa Haikal | 2506536465 | Sistem Informasi | [khansakkh](https://github.com/khansakkh) |
| Stefani Gwen Rolanda Tumbelaka | 2506594263 | Sistem Informasi | [stefanigwen14](https://github.com/stefanigwen14) |
| Muhammad Fatahillah Widodo | 2506623925 | Ilmu Komputer | [wmfatah](https://github.com/wmfatah) |
| Adinata Alaudin Pranaja | 2506656356 | Sistem Informasi | [adinatapranaja](https://github.com/adinatapranaja) |
| Angga Restha Rustyanto | 2506656444 | Ilmu Komputer | [AnggaRestha](https://github.com/AnggaRestha) |

## Rencana modul dan PIC

Pembagian tanggung jawab pengembangan modul kelompok C9 adalah sebagai berikut. Fitur di bawah merupakan rencana pengembangan; Checkpoint 1 masih berupa code base Django dan halaman roket.

| Modul | Deskripsi | PIC |
| --- | --- | --- |
| User & Authentication | Registrasi, login, logout, pengelolaan profil, serta peran dan pembatasan hak akses pengguna. | Adinata Alaudin Pranaja |
| Event Management | Membuat, melihat, mengubah, dan menghapus acara (CRUD), menampilkan detail acara, serta mengelola vendor terkait. Pencarian lokasi acara direncanakan menggunakan Nominatim. | Khansa Khairunnisa Haikal |
| Food Waste Reporting | Membuat dan melihat laporan serta detail makanan sisa, meliputi foto, jenis makanan, jumlah porsi, tenggat best before, lokasi, dan opsi penjemputan. | Stefani Gwen Rolanda Tumbelaka |
| Food Waste Management | Memverifikasi dan menerima atau menolak laporan, memperbarui status penanganan, serta menentukan tindak lanjut berupa penjualan, pembagian, atau pengolahan makanan. | Angga Restha Rustyanto |
| Discovery & Dashboard | Pencarian dan penyaringan makanan, dashboard, serta statistik laporan dan penanganan makanan. | Muhammad Fatahillah Widodo |

## Peran dan target pengguna

| Peran | Target pengguna | Hak akses yang direncanakan |
| --- | --- | --- |
| Admin Mode | EO/panitia dan tim pengelola FoodWaste | Mengelola acara, memeriksa foto dan informasi laporan, menerima atau menolak laporan, mengoordinasikan pengambilan, serta menentukan pengolahan, penjualan kembali, atau publikasi ulang makanan. |
| User Mode | Peserta acara yang sudah login | Melihat postingan, mengirim laporan ketersediaan makanan, dan mengajukan pengambilan makanan yang ditawarkan. |
| Pengunjung / Non-Role | Pengunjung yang belum login | Hanya melihat postingan; tidak dapat memposting laporan atau mengajukan pengambilan makanan. |

## Perbandingan aplikasi serupa

Surplus Indonesia dan Olio memiliki tujuan yang berkaitan dengan pengurangan pemborosan, tetapi pendekatannya berbeda dengan konsep FoodWaste.

| Aplikasi | Fokus dan mekanisme | Pembeda konsep FoodWaste |
| --- | --- | --- |
| Surplus Indonesia | Marketplace untuk penjualan stok berlebih dari mitra usaha kepada pelanggan. Mitra mengunggah produk melalui Surplus Merchant, sementara pelanggan membeli produk yang ditawarkan. Sumber: [Surplus Mitra](https://surplus.id/mitra/). | FoodWaste berangkat dari laporan peserta dalam suatu acara. Peserta dapat melaporkan makanan, lalu EO memeriksa dan menentukan tindak lanjutnya, termasuk opsi selain penjualan. |
| Olio | Berbagi makanan dan barang dalam komunitas lokal. Olio juga memiliki program Food Waste Heroes untuk pengambilan dan redistribusi makanan surplus dari bisnis. Sumber: [Olio](https://olioapp.com/en/) dan [Food Waste Heroes](https://olioapp.com/business/food-waste-heroes-programme/). | FoodWaste dirancang dengan acara sebagai pusat koordinasi: laporan peserta diteruskan ke admin EO untuk diperiksa, dijemput, dan ditangani atau ditawarkan kembali kepada peserta. |

Pembeda yang diusulkan adalah alur **peserta melapor → EO memoderasi → EO mengoordinasikan penanganan** dalam konteks acara yang sama. Perbandingan ini menekankan fokus rancangan FoodWaste, bukan klaim bahwa kompetitor tidak dapat melayani skala besar atau kegiatan katering. Fitur FoodWaste pada tabel masih berupa rencana pengembangan.

## Public API / mock API

Public API yang dipilih adalah **Nominatim**, layanan pencarian lokasi berdasarkan data OpenStreetMap. FoodWaste berencana memakainya pada modul Acara untuk mengubah nama tempat atau alamat yang dimasukkan EO menjadi pilihan lokasi beserta koordinat lintang dan bujur.

Alur penggunaan: EO mengetik nama tempat atau alamat acara → menekan tombol **Cari lokasi** → memilih hasil pencarian → aplikasi menyimpan alamat dan koordinat pada data acara. Detail internal acara, seperti nomor stan atau posisi pos pengumpulan, tetap diisi oleh EO.

- Sumber layanan: [Nominatim](https://nominatim.org/).
- Endpoint pencarian: `https://nominatim.openstreetmap.org/search` dengan parameter `q` dan `format=jsonv2`.
- Dokumentasi: [Search API](https://nominatim.org/release-docs/latest/api/Search/).
- Ketentuan: [Nominatim Usage Policy](https://operations.osmfoundation.org/policies/nominatim/).

Nominatim merupakan perangkat lunak open source dan layanan publiknya dapat digunakan tanpa biaya sesuai kebijakan penggunaan. Integrasi direncanakan melalui backend Django dengan pembatasan maksimal satu request per detik untuk seluruh aplikasi, identitas aplikasi pada User-Agent, penyimpanan hasil pencarian (cache), serta atribusi **© OpenStreetMap contributors** yang ditautkan ke [informasi hak cipta OpenStreetMap](https://www.openstreetmap.org/copyright). Pencarian hanya dijalankan saat tombol ditekan, bukan autocomplete setiap kali pengguna mengetik. Alamat layanan dibuat dapat dikonfigurasi agar bisa diganti bila diperlukan.

**Status Checkpoint 1:** API sudah dipilih sebagai rencana integrasi; belum diimplementasikan. Deployment saat ini tetap menampilkan halaman roket Django.

## Deployment PWS

[Buka deployment FoodWaste di PWS](https://adinata-alaudin51-foodwaste.pws.cs.ui.ac.id/)

Untuk Checkpoint 1, deployment menampilkan halaman roket bawaan Django. Telah diperiksa pada 15 September 2026: respons HTTP 200 dan halaman “The install worked successfully! Congratulations!”.

## Desain Figma

[Desain FoodWaste di Figma](https://www.figma.com/design/wSGPDUl78i7Bzpfz7zeWil/Untitled?node-id=0-1&t=KkgO6a6FgNbzobOW-1)

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
7. Buka tautan Deployment PWS di atas untuk memeriksa hasil deployment.

Konfigurasi PostgreSQL menggunakan schema `tugas_kelompok`; SQLite digunakan untuk pengembangan lokal dan database sementara di memori pada mode checkpoint. `.env`, database lokal, dan virtual environment tidak diikutkan ke Git.

Referensi setup: https://pbp.cs.ui.ac.id/tutorial/tutorial-0.html dan https://pbp.cs.ui.ac.id/tutorial/tutorial-1.html
