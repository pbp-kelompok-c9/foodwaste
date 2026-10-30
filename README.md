# 🍽️ FoodWastey 🗑️

Proyek Tengah Semester PBP C — Kelompok C9.

## ℹ️ Deskripsi Aplikasi

FoodWastey adalah aplikasi berbasis web yang dirancang untuk membantu mengurangi makanan terbuang pada acara melalui kerja sama dengan Event Organizer (EO). Aplikasi ini ditujukan untuk konser, acara keagamaan, kegiatan kampus, maupun acara berskala kecil. Makanan yang tidak termakan atau berlebih dapat dilaporkan oleh peserta agar penanganannya lebih teratur dan tidak langsung berakhir sebagai sampah.

Peserta yang sudah login dapat mengirim laporan ketersediaan makanan berisi foto, lokasi, jumlah porsi, tenggat waktu best before yang diketahui pelapor, dan opsi penjemputan. Admin dari pihak EO atau tim pengelola FoodWastey memeriksa laporan dan dapat menerima atau menolaknya apabila foto maupun informasi yang diberikan tidak sesuai ketentuan. Setelah laporan diterima dan kondisi makanan diperiksa, admin menentukan tindak lanjut berupa pengambilan, pengolahan, penjualan kembali, atau publikasi ulang untuk ditawarkan kepada peserta acara.

Nilai utama FoodWastey adalah menghubungkan laporan peserta dengan tindakan panitia dalam satu alur yang terpusat. Peserta mendapat cara praktis untuk melaporkan makanan, sementara EO dapat memantau ketersediaan dan proses penanganannya. Dengan demikian, aplikasi diharapkan membantu mengurangi makanan terbuang dan menjaga kebersihan lokasi setelah acara berakhir.

Alur aplikasi: peserta mengirim laporan → admin menerima atau menolak laporan → pemeriksaan dan penjemputan → admin menentukan penanganan atau menawarkan kembali makanan → selesai. Penerimaan laporan merupakan penerimaan untuk ditindaklanjuti, bukan sertifikasi kelayakan konsumsi. Kondisi makanan perlu diperiksa oleh petugas sebelum keputusan penanganan dibuat.

## ⚙️ Panduan Instalasi (Menjalankan Local)

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

Buka http://127.0.0.1:8000/ untuk membuka halaman Beranda FoodWastey. Hentikan server dengan Ctrl+C.

Untuk menjalankan seluruh unit test: `python manage.py test`.

## 🌐 Menyiapkan PWS

1. Proyek PWS bernama `foodwaste`.
2. Isi Environs berdasarkan `.env.prod.example` menggunakan kredensial database ITF salah satu anggota. Gunakan schema `tugas_kelompok` untuk proyek kelompok.
3. Buat SECRET_KEY acak melalui `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` lalu simpan hanya di PWS Environs.
4. Isi ALLOWED_HOSTS dengan hostname deployment yang benar dan CSRF_TRUSTED_ORIGINS dengan URL HTTPS-nya.
5. Ikuti Project Command PWS untuk menambahkan remote. Jangan cantumkan password dalam README atau commit.
6. Push dengan `git push pws main`, periksa status Running dan buka View Project.

Saat aplikasi dijalankan di PWS, `scripts/ensure_schema.py` membuat schema `tugas_kelompok` jika belum ada, lalu migration dijalankan otomatis sebelum gunicorn dimulai. PostgreSQL dipakai di PWS, sedangkan SQLite dipakai untuk pengembangan lokal. `.env`, database lokal, dan virtual environment tidak diikutkan ke Git.

### CI/CD

Repository ini memakai dua workflow GitHub Actions:

- **Django CI** (`.github/workflows/ci.yml`): menjalankan `manage.py check`, pengecekan migration, dan seluruh unit test pada setiap push ke `main`.
- **Push to PWS** (`.github/workflows/deploy.yml`): setiap push ke `main` otomatis diteruskan ke branch `main` di PWS, sehingga PWS selalu memakai versi terbaru tanpa push manual. Workflow ini membaca URL PWS beserta kredensialnya dari repository secret `PWS_URL`.

Referensi setup: https://pbp.cs.ui.ac.id/tutorial/tutorial-0.html dan https://pbp.cs.ui.ac.id/tutorial/tutorial-1.html

## 👥 Anggota kelompok

| Nama | NPM | Program Studi | GitHub |
| --- | --- | --- | --- |
| Khansa Khairunnisa Haikal | 2506536465 | Sistem Informasi | [khansakkh](https://github.com/khansakkh) |
| Stefani Gwen Rolanda Tumbelaka | 2506594263 | Sistem Informasi | [stefanigwen14](https://github.com/stefanigwen14) |
| Muhammad Fatahillah Widodo | 2506623925 | Ilmu Komputer | [wmfatah](https://github.com/wmfatah) |
| Adinata Alaudin Pranaja | 2506656356 | Sistem Informasi | [adinatapranaja](https://github.com/adinatapranaja) |
| Angga Restha Rustyanto | 2506656444 | Ilmu Komputer | [AnggaRestha](https://github.com/AnggaRestha) |

## 💻 Modul dan PIC

Pembagian tanggung jawab pengembangan modul kelompok C9 adalah sebagai berikut.

| Modul | Deskripsi | PIC |
| --- | --- | --- |
| User & Authentication | Registrasi, login (termasuk Masuk dengan Google), logout, pengelolaan profil, hapus akun, serta direktori pengguna dengan kontak yang hanya terlihat oleh pengguna yang sudah login. | Adinata Alaudin Pranaja |
| Event Management | Membuat, melihat, mengubah, dan menghapus acara (CRUD) oleh EO, menampilkan detail acara, serta pencarian lokasi acara menggunakan Nominatim. | Khansa Khairunnisa Haikal |
| Food Waste Reporting | Membuat dan melihat laporan serta detail makanan sisa, meliputi foto, jenis makanan, jumlah porsi, tenggat best before, lokasi, dan opsi penjemputan. | Stefani Gwen Rolanda Tumbelaka |
| Food Waste Management | Memverifikasi dan menerima atau menolak laporan, memperbarui status penanganan, serta menentukan tindak lanjut berupa penjualan, pembagian, atau pengolahan makanan. | Angga Restha Rustyanto |
| Discovery & Dashboard | Pencarian dan penyaringan makanan, pengajuan pengambilan makanan beserta unggah bukti pengambilan, dashboard, serta statistik laporan dan penanganan makanan. | Muhammad Fatahillah Widodo |

## 👤 Peran dan target pengguna

| Peran | Target pengguna | Hak akses |
| --- | --- | --- |
| EO | Penyelenggara acara dalam Group `EO`, tanpa memerlukan staff | Membuat acara, mengubah/menghapus acara miliknya, dan membuat laporan. Tidak otomatis mendapat akses Kelola laporan. |
| Admin Mode | Staff pengelola laporan | Memeriksa foto dan informasi laporan, menerima atau menolak laporan, mengoordinasikan pengambilan, serta menentukan tindak lanjut makanan. |
| User Mode | Peserta acara yang sudah login | Melihat postingan, mengirim laporan ketersediaan makanan, dan mengajukan pengambilan makanan yang ditawarkan. |
| Pengunjung / Non-Role | Pengunjung yang belum login | Hanya melihat postingan; tidak dapat memposting laporan atau mengajukan pengambilan makanan. |

## 📲 Perbandingan aplikasi serupa

Surplus Indonesia dan Olio memiliki tujuan yang berkaitan dengan pengurangan pemborosan, tetapi pendekatannya berbeda dengan konsep FoodWastey.

| Aplikasi | Fokus dan mekanisme | Pembeda konsep FoodWastey |
| --- | --- | --- |
| Surplus Indonesia | Marketplace untuk penjualan stok berlebih dari mitra usaha kepada pelanggan. Mitra mengunggah produk melalui Surplus Merchant, sementara pelanggan membeli produk yang ditawarkan. Sumber: [Surplus Mitra](https://surplus.id/mitra/). | FoodWaste berangkat dari laporan peserta dalam suatu acara. Peserta dapat melaporkan makanan, lalu EO memeriksa dan menentukan tindak lanjutnya, termasuk opsi selain penjualan. |
| Olio | Berbagi makanan dan barang dalam komunitas lokal. Olio juga memiliki program Food Waste Heroes untuk pengambilan dan redistribusi makanan surplus dari bisnis. Sumber: [Olio](https://olioapp.com/en/) dan [Food Waste Heroes](https://olioapp.com/business/food-waste-heroes-programme/). | FoodWaste dirancang dengan acara sebagai pusat koordinasi: laporan peserta diteruskan ke admin EO untuk diperiksa, dijemput, dan ditangani atau ditawarkan kembali kepada peserta. |

Pembeda yang diusulkan adalah alur **peserta melapor → EO memoderasi → EO mengoordinasikan penanganan** dalam konteks acara yang sama. Perbandingan ini menekankan fokus rancangan FoodWaste, bukan klaim bahwa kompetitor tidak dapat melayani skala besar atau kegiatan katering.

## 🌏 Public API / mock API

Public API yang digunakan adalah **Nominatim**, layanan pencarian lokasi berdasarkan data OpenStreetMap. FoodWastey memakainya pada modul Acara untuk mengubah nama tempat atau alamat yang dimasukkan EO menjadi pilihan lokasi beserta koordinat lintang dan bujur.

Alur penggunaan: EO mengetik nama tempat atau alamat acara → menekan tombol **Cari lokasi** → memilih hasil pencarian → aplikasi menyimpan alamat dan koordinat pada data acara. Detail internal acara, seperti nomor stan atau posisi pos pengumpulan, tetap diisi oleh EO.

- Sumber layanan: [Nominatim](https://nominatim.org/).
- Endpoint pencarian: `https://nominatim.openstreetmap.org/search` dengan parameter `q` dan `format=jsonv2`.
- Dokumentasi: [Search API](https://nominatim.org/release-docs/latest/api/Search/).
- Ketentuan: [Nominatim Usage Policy](https://operations.osmfoundation.org/policies/nominatim/).
- Deskripsi data: hasil *forward geocoding* berupa nama lokasi, alamat, serta koordinat lintang dan bujur. Koordinat yang disimpan dipakai untuk tautan **Lihat di OpenStreetMap** pada halaman detail acara.

Nominatim merupakan perangkat lunak open source dan layanan publiknya dapat digunakan tanpa biaya sesuai kebijakan penggunaan. Integrasi dilakukan melalui backend Django dengan pembatasan maksimal satu request per detik untuk seluruh aplikasi, identitas aplikasi pada User-Agent, penyimpanan hasil pencarian (cache), serta atribusi **© OpenStreetMap contributors** yang ditautkan ke [informasi hak cipta OpenStreetMap](https://www.openstreetmap.org/copyright). Pencarian hanya dijalankan saat tombol ditekan, bukan autocomplete setiap kali pengguna mengetik. Alamat layanan dibuat dapat dikonfigurasi agar bisa diganti bila diperlukan.

## 🌐 Deployment PWS

[Buka deployment FoodWastey di PWS](https://adinata-alaudin51-foodwaste.pws.cs.ui.ac.id/)

Deployment menjalankan aplikasi lengkap dengan database PostgreSQL ITF (schema `tugas_kelompok`) dan diperbarui otomatis melalui workflow CD setiap ada push ke `main`.

## 🎨 Desain Figma

[Desain FoodWastey di Figma](https://www.figma.com/design/wSGPDUl78i7Bzpfz7zeWil/Untitled?node-id=0-1&t=KkgO6a6FgNbzobOW-1)

## 🔐 Pengembangan Authentication

Registrasi, login, dan logout memakai User bawaan Django. Role EO memakai Group `EO`, terpisah dari staff Kelola laporan. Event Management menyediakan CRUD dengan ownership, pencarian lokasi, dan dropdown acara pada Reporting. Kolom teks acara laporan lama dipertahankan. Lihat [panduan authentication](docs/authentication.md), [panduan Event Management dan pengecekan di VS Code](docs/event-management.md), serta [acuan palet warna](docs/color-palette.md).

Pengelolaan profil sudah tersedia. Setiap akun otomatis memiliki profil saat dibuat, berisi nama tampilan, kota, bio, nomor HP, dan ID LINE. Pengguna yang sudah login dapat melihat profilnya di halaman **Profil saya** (`/profil/`), mengubah profil, dan menghapus akun. Perubahan profil disimpan secara asinkronus dengan AJAX tanpa memuat ulang halaman, dan pesan validasi ditampilkan langsung di bawah kolom yang salah. Penghapusan akun meminta konfirmasi berupa pengetikan ulang username. Akun admin tidak bisa dihapus dari halaman ini, begitu pula akun yang masih memiliki acara.

Halaman **Direktori pengguna** (`/pengguna/`) menampilkan daftar pengguna aktif yang dapat dicari berdasarkan nama atau username serta disaring berdasarkan kota, dengan 12 pengguna per halaman. Setiap pengguna juga memiliki halaman profil publik (`/pengguna/<username>/`). Nomor HP dan ID LINE hanya ditampilkan kepada pengguna yang sudah login; pengunjung lain diarahkan untuk masuk terlebih dahulu. Data yang sama tersedia dalam format JSON melalui `/api/profil/`, `/api/pengguna/`, dan `/api/pengguna/<username>/`, dengan aturan tampilan kontak yang sama.

## 📝 Pengembangan Food Waste Reporting

Setiap User yang sudah terautentikasi dapat membuat laporan. Operasi CRUD (menambahkan laporan, memperbarui laporan, menghapus laporan) dilakukan secara asinkronus dengan AJAX. User terautentikasi dapat membuat laporan dari halaman utama Laporan dengan mengklik tombol "+ Buat Laporan" dengan melakukan input foto, Nama Makanan, Porsi (maksimal 1000, jika lebih banyak disarankan membuat laporan terpisah), Waktu Kedaluwarsa (dengan format tanggal-bulan-tahun-jam-menit), Lokasi spesifik letak sisa makanan yang dilaporkan, Event (terintegrasi dengan modul Event, sehingga EO harus membuat Event sebelum pelapor dapat melaporkan), Opsi Penjemputan (diantar/ambil sendiri), serta Deskripsi Tambahan. Setelah ditambahkan, User dapat melihat feedback bahwa Laporan sudah ditambahkan dan laporan akan muncul sebagai kartu pada halaman utama Laporan. Laporan yang ditampilkan pada halaman utama Laporan hanya laporan yang dilaporkan oleh User yang sedang terautentikasi tersebut.

**AI Disclosure**: Modul ini dibantu pengembangannya dengan bantuan Claude AI. Pada sebagian besar pekerjaan, Claude membantu memberitahu contoh kode implementasi dalam modul ini yang akan tetap disesuaikan sendiri serta proses _debugging_. Beberapa kali iterasi _prompting_ diperlukan untuk memastikan implementasi yang sudah disesuaikan bisa benar-benar sesuai. Claude paling banyak membantu dalam proses JavaScript + AJAX untuk proses CRUD serta tampilan CSS. Claude juga membantu _generate_ unit tests yang terdapat pada modul ini sehingga mencapai 100% coverage.
[Lihat log _prompt_ di sini](https://claude.ai/share/019cde2a-aee8-4328-8fd3-c0d24e35c708)
