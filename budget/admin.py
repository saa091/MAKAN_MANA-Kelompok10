from django.contrib import admin
from .models import Profile, Kantin, Menu, Budget, Pesanan, ItemPesanan, ReviewMenu, Notifikasi, KeranjangItem

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role']
    list_filter = ['role']

@admin.register(Kantin)
class KantinAdmin(admin.ModelAdmin):
    list_display = ['nama_kantin', 'lokasi', 'status_keramaian', 'pemilik']

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ['nama_makanan', 'kantin', 'harga', 'stok_tersedia', 'jumlah_terjual']
    list_filter = ['stok_tersedia', 'kantin']

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'saldo', 'tanggal_update']

class ItemPesananInline(admin.TabularInline):
    model = ItemPesanan
    extra = 0

@admin.register(Pesanan)
class PesananAdmin(admin.ModelAdmin):
    list_display = ['id', 'mahasiswa', 'warung', 'total_harga', 'status', 'waktu_pesan']
    list_filter = ['status']
    inlines = [ItemPesananInline]

@admin.register(ReviewMenu)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['mahasiswa', 'menu', 'bintang', 'waktu_review', 'dilaporkan']
    list_filter = ['bintang', 'dilaporkan']

@admin.register(Notifikasi)
class NotifikasiAdmin(admin.ModelAdmin):
    list_display = ['user', 'judul', 'tipe', 'sudah_dibaca', 'waktu_kirim']
    list_filter = ['tipe', 'sudah_dibaca']

@admin.register(KeranjangItem)
class KeranjangAdmin(admin.ModelAdmin):
    list_display = ['user', 'menu', 'jumlah']