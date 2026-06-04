from .models import Notifikasi, ReviewMenu, KeranjangItem

def global_context(request):
    """
    Context processor: kirim notif_count, total_dilaporkan, jumlah_keranjang
    ke SEMUA template otomatis — sidebar tidak perlu tiap views mengirimnya.
    """
    if not request.user.is_authenticated:
        return {}

    ctx = {
        'notif_count': Notifikasi.objects.filter(
            user=request.user, sudah_dibaca=False
        ).count(),
    }

    try:
        role = request.user.profile.role
    except Exception:
        role = 'mahasiswa'

    if role == 'admin':
        ctx['total_dilaporkan'] = ReviewMenu.objects.filter(dilaporkan=True).count()
    else:
        ctx['jumlah_keranjang'] = KeranjangItem.objects.filter(user=request.user).count()

    return ctx