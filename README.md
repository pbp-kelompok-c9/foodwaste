# FoodWastey

Proyek Tengah Semester PBP C — Kelompok C9.

## Deskripsi aplikasi

FoodWastey adalah aplikasi berbasis web yang dirancang untuk membantu mengurangi makanan terbuang pada acara melalui kerja sama dengan Event Organizer (EO). Aplikasi ini ditujukan untuk konser, acara keagamaan, kegiatan kampus, maupun acara berskala kecil. Makanan yang tidak termakan atau berlebih dapat dilaporkan oleh peserta agar penanganannya lebih teratur dan tidak langsung berakhir sebagai sampah.

Peserta yang sudah login dapat mengirim laporan ketersediaan makanan berisi foto, lokasi, jumlah porsi, tenggat waktu best before yang diketahui pelapor, dan opsi penjemputan. Admin dari pihak EO atau tim pengelola FoodWastey memeriksa laporan dan dapat menerima atau menolaknya apabila foto maupun informasi yang diberikan tidak sesuai ketentuan. Setelah laporan diterima dan kondisi makanan diperiksa, admin menentukan tindak lanjut berupa pengambilan, pengolahan, penjualan kembali, atau publikasi ulang untuk ditawarkan kepada peserta acara.

Nilai utama FoodWastey adalah menghubungkan laporan peserta dengan tindakan panitia dalam satu alur yang terpusat. Peserta mendapat cara praktis untuk melaporkan makanan, sementara EO dapat memantau ketersediaan dan proses penanganannya. Dengan demikian, aplikasi diharapkan membantu mengurangi makanan terbuang dan menjaga kebersihan lokasi setelah acara berakhir.

Alur yang direncanakan: peserta mengirim laporan → admin menerima atau menolak laporan → pemeriksaan dan penjemputan → admin menentukan penanganan atau menawarkan kembali makanan → selesai. Penerimaan laporan merupakan penerimaan untuk ditindaklanjuti, bukan sertifikasi kelayakan konsumsi. Kondisi makanan perlu diperiksa oleh petugas sebelum keputusan penanganan dibuat.

## Status Checkpoint 1

Diperbarui pada 15 September 2026. Code base dan dokumentasi awal FoodWaste sudah tersedia dengan rincian berikut:

- [x] Repository `foodwaste` tersedia di GitHub Organization `pbp-kelompok-c9`.
- [x] Code base Django 5.2 tersedia.
- [x] Nama aplikasi, nama anggota, dan NPM seluruh anggota tercantum.
- [x] Deskripsi aplikasi dan nilai manfaatnya tercantum.
- [x] Perbandingan dengan Surplus Indonesia dan Olio dilengkapi sumber referensi.
- [x] Lima modul, deskripsi, dan PIC masing-masing sudah ditentukan.
- [x] Nominatim dipilih sebagai Public API; sumber dan rencana penggunaannya tercantum.
- [x] Peran pengguna dan target pengguna sudah dijelaskan.
- [x] [Deployment PWS](https://adinata-alaudin51-foodwaste.pws.cs.ui.ac.id/) berhasil menampilkan halaman roket Django.
- [x] [Tautan desain Figma](https://www.figma.com/design/wSGPDUl78i7Bzpfz7zeWil/Untitled?node-id=0-1&t=KkgO6a6FgNbzobOW-1) sudah dicantumkan.

Implementasi lima modul, integrasi Nominatim, dan konfigurasi database persisten merupakan pekerjaan pengembangan selanjutnya. Checklist ini mencatat ketersediaan hasil kerja dan dokumentasi, bukan konfirmasi pengumpulan atau penilaian tugas.

<details>
<summary>Catatan teknis deployment checkpoint</summary>

Secara bawaan `CHECKPOINT_ONLY=True`: hanya halaman roket, tanpa akun/admin atau database persisten; SQLite sementara di memori digunakan agar langkah migrasi otomatis PWS tetap berjalan tanpa kredensial database. Untuk mulai mengembangkan fitur, gunakan `.env.example` (`CHECKPOINT_ONLY=False`). Halaman `/` menampilkan halaman roket bawaan Django, termasuk ketika `PRODUCTION=True`. Route sementara ini menggunakan halaman bawaan Django, sehingga teks bawaannya tentang DEBUG tidak mencerminkan konfigurasi server.

</details>

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

Surplus Indonesia dan Olio memiliki tujuan yang berkaitan dengan pengurangan pemborosan, tetapi pendekatannya berbeda dengan konsep FoodWastey.

| Aplikasi | Fokus dan mekanisme | Pembeda konsep FoodWastey |
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

[Buka deployment FoodWastey di PWS](https://adinata-alaudin51-foodwaste.pws.cs.ui.ac.id/)

Untuk Checkpoint 1, deployment menampilkan halaman roket bawaan Django. Telah diperiksa pada 15 September 2026: respons HTTP 200 dan halaman “The install worked successfully! Congratulations!”.

## Desain Figma

[Desain FoodWastey di Figma](https://www.figma.com/design/wSGPDUl78i7Bzpfz7zeWil/Untitled?node-id=0-1&t=KkgO6a6FgNbzobOW-1)

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



## Sumber Public API (50 Initial Data)

Untuk memenuhi ketentuan minimal 50 initial data utama pada database aplikasi saat deployment, kami mengonsumsi data dari Public API eksternal berikut:

1. **DummyJSON Food/Recipes API**
   * **Tautan API:** `https://dummyjson.com/recipes?limit=50`
   * **Deskripsi Data:** Menyediakan 50 data objek makanan/resep secara langsung dalam format JSON, mencakup nama makanan, kategori, bahan-bahan, estimasi kalori, serta URL gambar makanan.
   * **Mekanisme Integrasi:** Data dari Public API ini di-*fetch* oleh skrip *seeding* Django (`seed_data.py`) untuk dimasukkan ke dalam database sebagai katalog awal *surplus food* sebelum aplikasi di-deploy ke PWS.

2. **TheMealDB API**
   * **Tautan API:** `https://www.themealdb.com/api/json/v1/1/search.php?s=`
   * **Deskripsi Data:** Menyediakan katalog data makanan lengkap beserta kategori, wilayah asal, instruksi, dan tautan gambar thumbnail makanan.
   * **Mekanisme Integrasi:** Digunakan sebagai alternatif sumber data *food catalog* yang di-*fetch* untuk memperkaya variasi *initial seed data*.

3. **OpenStreetMap (Nominatim API)**
   * **Tautan API:** `https://nominatim.openstreetmap.org/`
   * **Deskripsi Data:** Digunakan untuk *forward & reverse geocoding* dalam memetakan koordinat lokasi penjemputan makanan (latitude & longitude) secara visual pada peta interaktif Leaflet.js.
