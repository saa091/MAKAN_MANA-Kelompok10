# 🍽️ MAKAN MANA
**Aplikasi Web Pemesanan Makanan Kantin Kampus**

> Solusi digital untuk mempermudah mahasiswa dalam menemukan, memesan, dan membayar makanan di kantin kampus — lengkap dengan manajemen warung dan dashboard admin.

---

## 📋 Deskripsi Proyek

**MAKAN MANA** adalah aplikasi web berbasis Django yang dirancang untuk ekosistem kantin kampus. Aplikasi ini menghubungkan tiga jenis pengguna: **Mahasiswa**, **Pemilik Warung**, dan **Admin Kampus**, dalam satu platform terpadu.

Mahasiswa bisa melihat daftar kantin, memesan makanan secara pre-order, memantau status pesanan secara real-time, dan mengatur budget harian. Pemilik warung bisa mengelola menu dan memproses pesanan masuk. Admin kampus bisa memantau seluruh aktivitas platform.

---

## ✨ Fitur Utama

### 👨‍🎓 Mahasiswa
- Melihat daftar kantin beserta status keramaian (Sepi / Normal / Ramai)
- Browsing katalog menu dengan filter kategori (Makanan, Minuman, Snack, Paket)
- Sistem keranjang belanja & checkout
- Pre-order makanan dengan pelacakan status real-time
- Manajemen budget / saldo harian
- Riwayat pesanan & pemberian rating/review menu
- Sistem notifikasi (pesanan, budget, sistem)
- Manajemen profil

### 🏪 Pemilik Warung
- Dashboard warung dengan statistik penjualan
- Kelola menu (tambah, edit, hapus, atur stok)
- Proses pesanan masuk (Pending → Diproses → Siap Diambil → Selesai)
- Riwayat dan laporan transaksi warung
- Pengaturan profil warung

### 🛡️ Admin Kampus
- Dashboard monitoring seluruh platform
- Kelola data warung (verifikasi, nonaktifkan)
- Moderasi ulasan/review yang dilaporkan
- Laporan transaksi & aktivitas pengguna

---

## 🛠️ Tech Stack

| Komponen | Teknologi |
|---|---|
| Backend | Python 3.12 + Django |
| Database | MySQL (via XAMPP) |
| Frontend | HTML, CSS, Bootstrap, JavaScript |
| Template Engine | Django Templates |
| Auth | Django Built-in Auth + Role System |
| Media Storage | Django Media Files |
| Timezone | Asia/Makassar (WITA) |

---

## ⚙️ Instalasi & Menjalankan Proyek

### Prasyarat
Pastikan sudah terinstall:
- Python 3.10+ 
- XAMPP (untuk MySQL)
- pip

### Langkah Instalasi

**1. Clone / ekstrak repositori**
```bash
# Jika dari ZIP, ekstrak terlebih dahulu
# Masuk ke folder project
cd MAKAN_MANA/core
```

**2. Buat virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

**3. Install dependensi**
```bash
pip install django mysqlclient pillow
```

**4. Siapkan database MySQL**
- Jalankan XAMPP, aktifkan modul **Apache** dan **MySQL**
- Buka phpMyAdmin (`http://localhost/phpmyadmin`)
- Buat database baru bernama `makan_mana`

**5. Konfigurasi database** (opsional jika password MySQL bukan kosong)

Edit file `core/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'makan_mana',
        'USER': 'root',
        'PASSWORD': '',       # Ganti jika ada password
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
```

**6. Jalankan migrasi database**
```bash
python manage.py migrate
```

**7. Buat akun superuser (Admin)**
```bash
python manage.py createsuperuser
```

**8. Jalankan server**
```bash
python manage.py runserver
```

**9. Akses aplikasi**

Buka browser dan kunjungi: `http://127.0.0.1:8000/`

---

## 👤 Akun & Role

Setelah register, role default user adalah **Mahasiswa**. Untuk mengubah role:
1. Login ke Django Admin: `http://127.0.0.1:8000/admin/`
2. Buka tabel **Profile** → pilih user → ubah field `role`

| Role | Akses |
|---|---|
| `mahasiswa` | Dashboard mahasiswa, pesan makanan, atur budget |
| `pemilik` | Dashboard warung, kelola menu & pesanan |
| `admin` | Admin kampus, monitor seluruh platform |

---

## 📁 Struktur Proyek

```
MAKAN_MANA/
└── core/
    ├── manage.py
    ├── core/                  # Konfigurasi Django (settings, urls, wsgi)
    │   ├── settings.py
    │   └── urls.py
    ├── budget/                # App utama
    │   ├── models.py          # Model: Profile, Kantin, Menu, Pesanan, dll
    │   ├── views.py           # Semua view/logic
    │   ├── urls.py            # Routing URL
    │   ├── forms.py           # Form input
    │   ├── signals.py         # Django signals (auto-create profile, dll)
    │   ├── admin.py           # Konfigurasi Django Admin
    │   └── migrations/        # File migrasi database
    ├── templates/             # Template HTML
    │   ├── base.html
    │   ├── budget/            # Template semua halaman
    │   └── registration/      # Template login, register
    └── media/                 # File upload (gambar menu, foto profil)
        ├── menu_images/
        ├── profile_pics/
        └── warung_images/
```

---

## 🗄️ Model Database

| Model | Deskripsi |
|---|---|
| `Profile` | Ekstensi User dengan role (mahasiswa/pemilik/admin) |
| `Kantin` | Data warung/kantin kampus |
| `Menu` | Daftar menu tiap kantin |
| `Budget` | Saldo/budget mahasiswa |
| `KeranjangItem` | Item di keranjang belanja |
| `Pesanan` | Data pre-order mahasiswa |
| `ItemPesanan` | Detail item dalam satu pesanan |
| `ReviewMenu` | Rating & ulasan menu |
| `Notifikasi` | Notifikasi in-app untuk user |

---

## 📜 Lisensi

Proyek ini dibuat untuk keperluan Tugas Akhir akademik.  
Bebas digunakan dan dimodifikasi untuk tujuan pendidikan.

---

## 👥 Tim Pengembang

## 👥 Tim Pengembang

| Nama | NIM | Role |
|---|---|---|
| Agistha Aulia Nur Afifah | 2411102441145 | Admin |
| Isnaini Nur Laila Hayati | 2411102441155 | Pengguna (Mahasiswa) |
| Virni Yunike | 2411102441130 | Pemilik Warung |
| Hikma Herdis | 2411102441135 | Pemilik Warung |
| Naya Sascia Maulita | 2411102441139 | Pemilik Warung |