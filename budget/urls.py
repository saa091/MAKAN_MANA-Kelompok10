from django.urls import path
from . import views

urlpatterns = [
    # =====================
    # AUTHENTICATION
    # =====================
    path('register/', views.register, name='register'),
    path('lupa-password/', views.lupa_password, name='lupa_password'),  
    path('redirect/', views.smart_redirect, name='smart_redirect'),

    # Dashboard Utama
    path('', views.index, name='index'),

    # Budget Management
    path('atur-budget/', views.atur_budget, name='atur_budget'),

    # =====================
    # KANTIN & MENU
    # =====================
    path('kantin/', views.daftar_kantin, name='daftar_kantin'),
    path('kantin/<int:kantin_id>/', views.kantin_detail, name='kantin_detail'),
    path('kantin/<int:kantin_id>/menu/', views.katalog_menu, name='katalog_menu'),
    path('menu/<int:menu_id>/', views.detail_menu, name='detail_menu'),

    # =====================
    # KERANJANG BELANJA
    # =====================
    path('keranjang/', views.keranjang, name='keranjang'),
    path('keranjang/tambah/<int:menu_id>/', views.tambah_keranjang, name='tambah_keranjang'),
    path('keranjang/hapus/<int:item_id>/', views.hapus_keranjang, name='hapus_keranjang'),
    path('keranjang/update/<int:item_id>/', views.update_keranjang, name='update_keranjang'),
    path('keranjang/checkout/', views.checkout_keranjang, name='checkout_keranjang'),

    # =====================
    # PESANAN MAHASISWA
    # =====================
    path('pilih-menu/<int:menu_id>/', views.pilih_menu, name='pilih_menu'),
    path('status-pesanan/', views.status_pesanan, name='status_pesanan'),
    path('konfirmasi-selesai/<int:pesanan_id>/', views.konfirmasi_selesai, name='konfirmasi_selesai'),

    # =====================
    # NOTIFIKASI SYSTEM
    # =====================
    path('notifikasi/', views.notifikasi, name='notifikasi'),
    path('notifikasi/baca/<int:notif_id>/', views.tandai_baca, name='tandai_baca'),

    # =====================
    # RIWAYAT & REVIEW
    # =====================
    path('riwayat/', views.riwayat, name='riwayat'),
    path('review/<int:pesanan_id>/', views.beri_review, name='beri_review'),

    # =====================
    # PROFIL USER
    # =====================
    path('profil/', views.profil, name='profil'),
    path('ganti-password/', views.ganti_password, name='ganti_password'),

    # =====================
    # PEMILIK WARUNG / KANTIN
    # =====================
    path('dashboard-warung/', views.dashboard_warung, name='dashboard_warung'),
    path('manage-menu/', views.manage_menu, name='manage_menu'),
    path('tambah-menu/', views.tambah_menu, name='tambah_menu'),
    path('edit-menu/<int:menu_id>/', views.edit_menu, name='edit_menu'),
    path('hapus-menu/<int:menu_id>/', views.hapus_menu, name='hapus_menu'),
    path('toggle-stok/<int:menu_id>/', views.toggle_stok, name='toggle_stok'),
    path('kelola-pesanan/', views.kelola_pesanan, name='kelola_pesanan'),
    path('pesanan/<int:pesanan_id>/', views.detail_pesanan_pemilik, name='detail_pesanan_pemilik'),
    path('update-status/<int:pesanan_id>/', views.update_status_pesanan, name='update_status_pesanan'),
    path('pengaturan-warung/', views.pengaturan_warung, name='pengaturan_warung'),
    path('riwayat-warung/', views.riwayat_warung, name='riwayat_warung'),

    # =====================
    # ADMIN KAMPUS
    # =====================
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-kelola-warung/', views.admin_kelola_warung, name='admin_kelola_warung'),
    path('admin-laporan/', views.admin_laporan, name='admin_laporan'),
    path('admin-moderasi/', views.admin_moderasi, name='admin_moderasi'),
    path('review/laporkan/<int:review_id>/', views.laporkan_review, name='laporkan_review'),
]