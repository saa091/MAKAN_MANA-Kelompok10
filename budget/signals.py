from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Pesanan, ReviewMenu, Kantin, Profile


def buat_notif(user, judul, pesan, tipe='sistem', link=''):
    from .models import Notifikasi
    Notifikasi.objects.create(user=user, judul=judul, pesan=pesan, tipe=tipe, link=link)


def notif_ke_semua_admin(judul, pesan, tipe='sistem', link=''):
    from .models import Notifikasi
    admin_users = User.objects.filter(profile__role='admin')
    for admin in admin_users:
        Notifikasi.objects.create(user=admin, judul=judul, pesan=pesan, tipe=tipe, link=link)


# -------------------------------------------------------
# 1. Pesanan baru → notif ke admin (monitoring)
# -------------------------------------------------------
@receiver(post_save, sender=Pesanan)
def notif_pesanan_baru_ke_admin(sender, instance, created, **kwargs):
    if created:
        notif_ke_semua_admin(
            judul="Ada Pesanan Baru!",
            pesan=(
                f"{instance.mahasiswa.username} memesan dari "
                f"'{instance.warung.nama_kantin}' — Pesanan #{instance.id} "
                f"(Rp {instance.total_harga:,})"
            ),
            tipe='pesanan',
            link='/admin-dashboard/',
        )


# -------------------------------------------------------
# 2. Pesanan dibatalkan pemilik → notif ke admin
# -------------------------------------------------------
@receiver(post_save, sender=Pesanan)
def notif_pesanan_dibatalkan_ke_admin(sender, instance, created, **kwargs):
    if not created and instance.status == 'dibatalkan':
        notif_ke_semua_admin(
            judul="Pesanan Dibatalkan",
            pesan=(
                f"Pesanan #{instance.id} oleh {instance.mahasiswa.username} "
                f"di '{instance.warung.nama_kantin}' telah dibatalkan."
            ),
            tipe='pesanan',
            link='/admin-dashboard/',
        )


# -------------------------------------------------------
# 3. Review baru → notif ke admin jika bintang 1 atau 2
#    (early warning: review buruk masuk tanpa harus dilaporkan)
# -------------------------------------------------------
@receiver(post_save, sender=ReviewMenu)
def notif_review_buruk_ke_admin(sender, instance, created, **kwargs):
    if created and instance.bintang <= 2:
        notif_ke_semua_admin(
            judul="Review Bintang Rendah",
            pesan=(
                f"{instance.mahasiswa.username} memberi {instance.bintang} bintang "
                f"untuk menu '{instance.menu.nama_makanan}' "
                f"di warung '{instance.menu.kantin.nama_kantin}'."
            ),
            tipe='review',
            link='/admin-moderasi/?tab=semua',
        )