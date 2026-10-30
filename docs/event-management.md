# Event Management

Modul ini melanjutkan model dan form Event yang sudah ada. Peserta dapat memilih
acara yang dibuat EO ketika mengirim laporan. Kelola laporan tetap memakai akses
staff yang terpisah dari keanggotaan EO.

## Menjalankan dari VS Code di Windows

Buka folder `C:\Users\Lenovo\foodwaste-kelompok`, lalu buka **Terminal → New Terminal**.
Gunakan interpreter `.venv\Scripts\python.exe` melalui **Python: Select Interpreter**.
Jika belum ada environment/dependency, buat environment dan instal `requirements.txt`
terlebih dahulu. Perintah berikut memakai environment proyek secara langsung,
sehingga tidak perlu mengubah kebijakan PowerShell untuk aktivasi:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py showmigrations
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py test
node --test event_management/js_tests/location-search.test.cjs
.\.venv\Scripts\python.exe manage.py runserver
```

Sebelum menerapkan migration pada SQLite lokal yang sudah berisi data, hentikan
aplikasi dan salin `db.sqlite3` ke lokasi cadangan. Untuk PostgreSQL, gunakan backup
database dan konfigurasi environment deployment yang biasa digunakan tim.
Migration Reporting menambah kolom relasi yang boleh kosong dan mempertahankan
kolom teks acara lama; tidak menghapus laporan atau membuat akun pemilik acara
buatan. Gunakan database persisten yang sama untuk semua worker aplikasi.

## Menetapkan akun EO

Migration menyediakan Group bernama `EO`. Registrasi biasa dan login Google tidak
memberikan keanggotaan ini. Admin yang berwenang dapat menambahkan akun melalui
**Django admin → Users → Groups → EO**, tanpa mencentang **Staff status** pada akun EO.
Admin Django memerlukan akun admin tersendiri; akun EO tidak perlu akses admin Django.
Superuser dapat langsung membuat dan mengelola semua acara melalui menu Acara,
tanpa perlu menjadi anggota Group `EO`.

Alternatif melalui terminal admin lokal:

```powershell
.\.venv\Scripts\python.exe manage.py shell
```

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
eo = get_user_model().objects.get(username="nama_akun_eo")
eo.groups.add(Group.objects.get(name="EO"))
print(eo.is_staff, eo.groups.filter(name="EO").exists())
```

Untuk akun EO biasa, keluaran yang diharapkan adalah `False True`. Jangan mengambil
role dari input formulir registrasi atau parameter permintaan.

Jika akun yang dituju sebelumnya sudah memiliki staff, lepaskan staff melalui
admin terlebih dahulu bila akun itu memang harus menjadi EO biasa. Menambahkan
Group EO tidak mengubah hak staff yang sudah ada.

| Akun | Daftar/detail acara | Tambah acara | Ubah/hapus acara | Kelola laporan |
| --- | --- | --- | --- | --- |
| Pengunjung | Ya | Tidak | Tidak | Tidak |
| Peserta login | Ya | Tidak | Tidak | Tidak |
| EO tanpa staff | Ya | Ya | Acara miliknya | Tidak |
| Staff tanpa Group EO, bukan superuser | Ya | Tidak | Tidak | Ya |
| Superuser tanpa Group EO | Ya | Ya | Semua acara | Ya |

Pemeriksaan role dan pemilik dijalankan pada server untuk setiap aksi. Field
`created_by` ditetapkan dari akun login dan tidak dapat dipilih dari formulir.
Saat superuser mengedit acara milik EO, akun pemilik acara tetap dipertahankan.
Acara yang sudah dipakai laporan dilindungi dari penghapusan agar riwayat tetap ada.

Acara baru tidak boleh memakai tanggal dan waktu yang sudah lewat menurut WIB.
Pemilih tanggal memiliki batas minimum, dan server memeriksa ulang saat formulir
disimpan, dengan ketelitian satu menit. Tanggal acara lama yang tidak diubah tetap
dipertahankan saat mengedit keterangan; jika dijadwalkan ulang, waktu barunya harus
sekarang atau di masa mendatang. Perubahan ini tidak memerlukan migration.

## Alur pengecekan manual

1. Buka `/events/` tanpa login; daftar dan detail acara dapat dibaca.
2. Masuk sebagai peserta; formulir tambah acara dan aksi perubahan ditolak.
3. Masuk sebagai EO tanpa staff; tambah acara beserta tanggal, lokasi, dan deskripsi.
4. Ubah acara tersebut, lalu coba URL edit/hapus sebagai EO lain; akses ditolak.
5. Buka `/reporting/` sebagai peserta atau EO dan buat laporan dengan memilih acara.
6. Buka detail laporan dan Discovery; nama acara tampil. Laporan lama tetap
   menampilkan teks acara sebelumnya walaupun relasinya belum diisi.
7. Coba hapus acara yang sudah digunakan laporan; acara dan laporan tetap tersimpan.
8. Coba buka `/management/` sebagai EO tanpa staff; akses ditolak. Masuk sebagai
   staff untuk memeriksa laporan baru pada antrean verifikasi.
9. Masuk sebagai superuser yang tidak berada dalam Group `EO`; tombol tambah,
   edit, dan hapus tersedia, termasuk untuk acara milik akun lain. Acara yang
   sudah terhubung ke laporan tetap tidak dapat dihapus.

Laporan baru menyimpan relasi `related_event` dan nama acara sebagai snapshot di
kolom `event`. Tampilan memakai nama Event terhubung, dengan fallback ke teks lama
untuk laporan yang belum memiliki relasi. Tidak ada pencocokan otomatis nama lama
ke Event karena nama yang sama belum tentu menunjuk acara yang sama.

## Pencarian lokasi OpenStreetMap

Pencarian dijalankan EO atau superuser dengan menekan **Cari lokasi** pada formulir Event.
Backend memanggil Nominatim, lalu pengguna memilih hasil untuk mengisi alamat.
Latitude dan longitude tersimpan otomatis dalam field tersembunyi, sehingga EO
tidak perlu melihat atau mengisi koordinat secara manual. Alamat tetap bisa
ditulis manual ketika layanan tidak tersedia; dalam kasus itu titik peta boleh
kosong. Hasil maksimal lima lokasi, koordinat divalidasi dan dibulatkan ke enam
angka desimal. Tidak ada permintaan eksternal dari tests.

Penggunaan server publik mengikuti [Nominatim Usage Policy](https://operations.osmfoundation.org/policies/nominatim/):
beban ringan, maksimal satu permintaan per detik untuk seluruh aplikasi, identitas
aplikasi melalui User-Agent, cache hasil, atribusi OpenStreetMap, dan pencarian
manual tanpa autocomplete. Fitur ini dipakai khusus untuk alamat acara; jangan
mengirim data pribadi atau rahasia. Data hasil mengikuti ODbL. Kebijakan layanan
dapat berubah dan pengelola aplikasi bertanggung jawab meninjaunya sebelum deployment.

`LocationSearchState` menyimpan cache database selama 24 jam, termasuk hasil kosong,
serta satu gerbang permintaan bersama semua worker. Permintaan baru memperoleh
lease atomik, dibatasi waktu/besar respons, lalu memberi jeda satu detik setelah
selesai. Saat gerbang sibuk, endpoint mengembalikan HTTP 429 dan `Retry-After`;
tidak membuat antrean permintaan ke penyedia. Batas upstream 429 juga menahan
pencarian sesuai `Retry-After` yang dibatasi sampai satu jam. Masalah provider atau
database menghasilkan pesan agar pengguna bisa mengisi alamat manual.

Environment yang tersedia:

```dotenv
NOMINATIM_USER_AGENT=FoodWastey/1.0 (+https://github.com/pbp-kelompok-c9/foodwaste)
NOMINATIM_SEARCH_URL=https://nominatim.openstreetmap.org/search
```

Atur identitas/kontak User-Agent sesuai deployment. URL harus HTTPS dan dapat diganti
ke instance Nominatim milik sendiri atau provider yang kompatibel tanpa mengubah
kode. Untuk banyak pengguna, pilih layanan yang kapasitasnya sesuai. Endpoint
internal `/events/locations/search/?q=...` hanya menerima akun EO atau superuser; URL provider
ditetapkan di server, bukan dari input pengguna.

Referensi parameter: [Nominatim Search API](https://nominatim.org/release-docs/latest/api/Search/).
Atribusi pada form dan tautan lokasi: [© OpenStreetMap contributors](https://www.openstreetmap.org/copyright).
