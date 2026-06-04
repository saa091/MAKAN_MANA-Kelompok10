from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg, F, ExpressionWrapper, IntegerField
from django.db.models.functions import TruncDate, TruncMonth, Coalesce
from django.http import JsonResponse
from .models import (
    Menu, Kantin, Budget, Pesanan, ItemPesanan,
    Notifikasi, Profile, KeranjangItem, ReviewMenu
)
import json
from django.db.models.functions import TruncDate, TruncMonth
from django.core.serializers.json import DjangoJSONEncoder
from datetime import timedelta

# ==========================================
# HELPER
# ==========================================
def buat_notif(user, judul, pesan, tipe='sistem', link=''):
    Notifikasi.objects.create(user=user, judul=judul, pesan=pesan, tipe=tipe, link=link)

def notif_ke_semua_admin(judul, pesan, tipe='sistem', link=''):
    admin_users = User.objects.filter(profile__role='admin')
    for admin in admin_users:
        Notifikasi.objects.create(user=admin, judul=judul, pesan=pesan, tipe=tipe, link=link)

def is_pemilik(user):
    try:
        return user.profile.role == 'pemilik'
    except Profile.DoesNotExist:
        return False

def is_admin(user):
    try:
        return user.profile.role == 'admin'
    except Profile.DoesNotExist:
        return False
    
def get_pesanan_pending_count(user):
    return Pesanan.objects.filter(
        warung__pemilik=user, status='pending'
    ).count()

# ==========================================
# 1. AUTHENTICATION
# ==========================================
def register(request):
    try:
        from .forms import RegisterForm
        FormClass = RegisterForm
    except ImportError:
        FormClass = UserCreationForm

    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if hasattr(form.cleaned_data, 'get'):
                user.email = form.cleaned_data.get('email', '')
            user.save()
            Profile.objects.get_or_create(user=user, defaults={'role': 'mahasiswa'})
            Budget.objects.get_or_create(user=user, defaults={'saldo': 0})

            notif_ke_semua_admin(
                "Akun Baru Terdaftar",
                f"Mahasiswa baru '{user.username}' baru saja mendaftar.",
                tipe='sistem',
                link=reverse('budget:admin_dashboard')
            )

            messages.success(request, 'Akun berhasil dibuat! Silakan login.')
            return redirect('login')
    else:
        form = FormClass()
    return render(request, 'registration/register.html', {'form': form})


def lupa_password(request):
    try:
        from .forms import VerifikasiEmailForm, ResetPasswordForm
    except ImportError:
        messages.error(request, "Fitur lupa password belum tersedia.")
        return redirect('login')

    if request.method == 'POST' and request.POST.get('tahap') == '2':
        email = request.POST.get('email', '').strip()
        form2 = ResetPasswordForm(request.POST)
        if form2.is_valid():
            user = User.objects.filter(email__iexact=email).first()
            if user:
                user.set_password(form2.cleaned_data['password1'])
                user.save()
                return render(request, 'registration/lupa_password.html', {
                    'success': True,
                    'success_username': user.username,
                })
        return render(request, 'registration/lupa_password.html', {
            'step2': True, 'verified_email': email, 'form2': form2,
        })

    if request.method == 'POST' and request.POST.get('tahap') == '1':
        form = VerifikasiEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            return render(request, 'registration/lupa_password.html', {
                'step2': True, 'verified_email': email, 'form2': ResetPasswordForm(),
            })
        return render(request, 'registration/lupa_password.html', {'form': form})

    return render(request, 'registration/lupa_password.html', {
        'form': VerifikasiEmailForm(),
    })


def smart_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')
    try:
        role = request.user.profile.role
    except Exception:
        role = 'mahasiswa'
    if role == 'admin':
        return redirect('budget:admin_dashboard')
    if role == 'pemilik':
        return redirect('budget:dashboard_warung')
    return redirect('budget:index')  

# ==========================================
# 2. DASHBOARD MAHASISWA
# ==========================================
@login_required
def index(request):
    try:
        role = request.user.profile.role
        if role == 'admin':
            return redirect('budget:admin_dashboard')
        if role == 'pemilik':
            return redirect('budget:dashboard_warung')
    except Exception:
        pass

    budget_data, _ = Budget.objects.get_or_create(user=request.user)
    saldo_aktif = budget_data.saldo
    notifikasis = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False)[:5]
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
    pesanan_aktif = Pesanan.objects.filter(
        mahasiswa=request.user, status__in=['pending', 'diproses', 'siap']
    ).order_by('-waktu_pesan')

    if saldo_aktif > 0:
        menus = Menu.objects.filter(harga__lte=saldo_aktif, stok_tersedia=True).order_by('harga')
    else:
        menus = Menu.objects.filter(stok_tersedia=True).order_by('-id')

    rekomendasi = Menu.objects.filter(stok_tersedia=True).order_by('-jumlah_terjual')[:3]
    jumlah_keranjang = KeranjangItem.objects.filter(user=request.user).count()

    return render(request, 'budget/index.html', {
        'menus': menus,
        'budget': saldo_aktif,
        'notifikasis': notifikasis,
        'notif_count': notif_count,
        'pesanan_aktif': pesanan_aktif,
        'rekomendasi': rekomendasi,
        'daftar_kantin': Kantin.objects.all(),
        'jumlah_keranjang': jumlah_keranjang,
    })

# ==========================================
# 3. ATUR BUDGET
# ==========================================
@login_required
def atur_budget(request):
    budget_data, _ = Budget.objects.get_or_create(user=request.user)
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
    jumlah_keranjang = KeranjangItem.objects.filter(user=request.user).count()

    if request.method == 'POST':
        nominal = request.POST.get('budget_input', '').strip().replace('.', '').replace(',', '')

        if not nominal:
            messages.warning(request, "Nominal tidak boleh kosong.")
            return redirect('budget:atur_budget')

        try:
            nominal = int(nominal)
        except ValueError:
            messages.warning(request, "Nominal tidak valid. Masukkan angka yang benar.")
            return redirect('budget:atur_budget')

        if nominal <= 0:
            messages.warning(request, "Nominal harus lebih dari Rp 0.")
            return redirect('budget:atur_budget')

        if nominal > 500000:
            messages.warning(request, "Nominal maksimal adalah Rp 500.000 per pengisian.")
            return redirect('budget:atur_budget')

        saldo_sebelum = budget_data.saldo
        budget_data.saldo = saldo_sebelum + nominal
        budget_data.save()

        buat_notif(request.user, "Budget Diperbarui",
            f"Kamu berhasil menambahkan Rp {nominal:,}. Saldo sekarang: Rp {budget_data.saldo:,}",
            tipe='budget')
        messages.success(request, f"Berhasil menambahkan Rp {nominal:,}. Saldo kamu sekarang Rp {budget_data.saldo:,}!")
        return redirect('budget:index')

    return render(request, 'budget/atur_budget.html', {
        'budget': budget_data.saldo,
        'notif_count': notif_count,
        'jumlah_keranjang': jumlah_keranjang,
    })

# ==========================================
# 4. DAFTAR KANTIN
# ==========================================
@login_required
def daftar_kantin(request):
    kantins = Kantin.objects.all()
    budget_data, _ = Budget.objects.get_or_create(user=request.user)
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
    jumlah_keranjang = KeranjangItem.objects.filter(user=request.user).count()
    return render(request, 'budget/daftar_kantin.html', {
        'kantins': kantins, 'budget': budget_data.saldo,
        'notif_count': notif_count, 'jumlah_keranjang': jumlah_keranjang,
    })

# ==========================================
# 5. KATALOG MENU
# ==========================================
@login_required
def katalog_menu(request, kantin_id):
    kantin = get_object_or_404(Kantin, id=kantin_id)
    budget_data, _ = Budget.objects.get_or_create(user=request.user)
    saldo = budget_data.saldo
    menus = Menu.objects.filter(kantin=kantin, stok_tersedia=True)
    filter_budget = request.GET.get('filter_budget')
    if filter_budget == '1' and saldo > 0:
        menus = menus.filter(harga__lte=saldo)
    label_filter = request.GET.get('label', '')
    if label_filter:
        menus = menus.filter(label__icontains=label_filter)
    semua_label = Menu.objects.filter(kantin=kantin).values_list('label', flat=True).distinct()
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
    jumlah_keranjang = KeranjangItem.objects.filter(user=request.user).count()
    return render(request, 'budget/katalog_menu.html', {
        'kantin': kantin, 'menus': menus, 'budget': saldo,
        'filter_budget': filter_budget, 'label_filter': label_filter,
        'semua_label': semua_label, 'notif_count': notif_count,
        'jumlah_keranjang': jumlah_keranjang,
    })

# ==========================================
# 6. DETAIL MENU
# ==========================================
@login_required
def detail_menu(request, menu_id):
    menu = get_object_or_404(Menu, id=menu_id)
    reviews = ReviewMenu.objects.filter(menu=menu).order_by('-waktu_review')
    budget_data, _ = Budget.objects.get_or_create(user=request.user)
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
    jumlah_keranjang = KeranjangItem.objects.filter(user=request.user).count()
    avg_rating = menu.avg_rating()
    return render(request, 'budget/detail_menu.html', {
        'menu': menu, 'reviews': reviews, 'budget': budget_data.saldo,
        'avg_rating': avg_rating, 'notif_count': notif_count,
        'jumlah_keranjang': jumlah_keranjang,
    })

# ==========================================
# 7. KERANJANG
# ==========================================
@login_required
def keranjang(request):
    items = KeranjangItem.objects.filter(user=request.user).select_related('menu__kantin')
    budget_data, _ = Budget.objects.get_or_create(user=request.user)
    total = sum(i.subtotal() for i in items)
    sisa_budget = budget_data.saldo - total
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
    return render(request, 'budget/keranjang.html', {
        'items': items, 'total': total, 'budget': budget_data.saldo,
        'sisa_budget': sisa_budget, 'notif_count': notif_count,
        'jumlah_keranjang': items.count(),
    })

@login_required
def tambah_keranjang(request, menu_id):
    menu = get_object_or_404(Menu, id=menu_id)
    catatan = request.POST.get('catatan', '')
    jumlah = int(request.POST.get('jumlah', 1))
    item, created = KeranjangItem.objects.get_or_create(
        user=request.user, menu=menu,
        defaults={'catatan_item': catatan, 'jumlah': jumlah}
    )
    if not created:
        item.jumlah += jumlah
        item.save()
    messages.success(request, f"{menu.nama_makanan} ditambahkan ke keranjang!")
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
    return redirect(next_url)

@login_required
def hapus_keranjang(request, item_id):
    item = get_object_or_404(KeranjangItem, id=item_id, user=request.user)
    item.delete()
    messages.info(request, "Item dihapus dari keranjang.")
    return redirect('budget:keranjang')

@login_required
def update_keranjang(request, item_id):
    item = get_object_or_404(KeranjangItem, id=item_id, user=request.user)
    jumlah = int(request.POST.get('jumlah', 1))
    if jumlah <= 0:
        item.delete()
    else:
        item.jumlah = jumlah
        item.save()
    return redirect('budget:keranjang')

@login_required
def checkout_keranjang(request):
    items = KeranjangItem.objects.filter(user=request.user)
    if not items.exists():
        messages.error(request, "Keranjang masih kosong!")
        return redirect('budget:keranjang')
    budget_data, _ = Budget.objects.get_or_create(user=request.user)
    total = sum(i.subtotal() for i in items)
    if budget_data.saldo < total:
        messages.error(request, f"Budget tidak cukup! Total Rp {total:,}, saldo Rp {budget_data.saldo:,}")
        return redirect('budget:keranjang')
    warung_dict = {}
    for item in items:
        wid = item.menu.kantin.id
        if wid not in warung_dict:
            warung_dict[wid] = {'kantin': item.menu.kantin, 'items': []}
        warung_dict[wid]['items'].append(item)
    for wid, data in warung_dict.items():
        subtotal_warung = sum(i.subtotal() for i in data['items'])
        pesanan = Pesanan.objects.create(
            mahasiswa=request.user, warung=data['kantin'],
            total_harga=subtotal_warung, status='pending',
        )
        for item in data['items']:
            ItemPesanan.objects.create(
                pesanan=pesanan, menu=item.menu, jumlah=item.jumlah,
                harga_saat_pesan=item.menu.harga, catatan_item=item.catatan_item
            )
            item.menu.jumlah_terjual += item.jumlah
            item.menu.save()

        if data['kantin'].pemilik:
            buat_notif(
                data['kantin'].pemilik,
                "Ada Pesanan Baru!",
                f"{request.user.username} memesan Rp {subtotal_warung:,} dari warungmu — Pesanan #{pesanan.id}",
                tipe='pesanan',
                link=reverse('budget:detail_pesanan_pemilik', args=[pesanan.id])
            )

        buat_notif(
            request.user,
            "Pesanan Berhasil Dibuat!",
            f"Pesanan #{pesanan.id} di {data['kantin'].nama_kantin} sedang menunggu konfirmasi warung.",
            tipe='pesanan',
            link=f"{reverse('budget:status_pesanan')}?highlight={pesanan.id}"
        )

        notif_ke_semua_admin(
            "Pesanan Masuk Baru",
            f"{request.user.username} memesan Rp {subtotal_warung:,} di {data['kantin'].nama_kantin} — Pesanan #{pesanan.id}",
            tipe='pesanan',
            link=reverse('budget:admin_laporan')
        )

    budget_data.saldo -= total
    budget_data.save()
    items.delete()
    messages.success(request, "Pesanan berhasil dikirim ke warung!")
    return redirect('budget:status_pesanan')

# ==========================================
# 8. STATUS PESANAN (MAHASISWA)
# ==========================================
@login_required
def status_pesanan(request):
    pesanan_list = Pesanan.objects.filter(mahasiswa=request.user).order_by('-waktu_pesan')
    budget_data, _ = Budget.objects.get_or_create(user=request.user)
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
    jumlah_keranjang = KeranjangItem.objects.filter(user=request.user).count()
    highlight_id = request.GET.get('highlight', '')
    return render(request, 'budget/status_pesanan.html', {
        'pesanan_list': pesanan_list,
        'budget': budget_data.saldo,
        'notif_count': notif_count,
        'jumlah_keranjang': jumlah_keranjang,
        'highlight_id': highlight_id,
    })

@login_required
def konfirmasi_selesai(request, pesanan_id):
    pesanan = get_object_or_404(Pesanan, id=pesanan_id, mahasiswa=request.user)
    if pesanan.status == 'siap':
        pesanan.status = 'selesai'
        pesanan.waktu_selesai = timezone.now()
        pesanan.save()
        if pesanan.warung.pemilik:
            buat_notif(
                pesanan.warung.pemilik,
                "Pesanan Dikonfirmasi Selesai",
                f"Pesanan #{pesanan.id} sudah diambil oleh {request.user.username}.",
                tipe='pesanan',
                link=reverse('budget:detail_pesanan_pemilik', args=[pesanan.id])
            )
        messages.success(request, "Pesanan dikonfirmasi selesai! Silakan beri review.")
        return redirect('budget:beri_review', pesanan_id=pesanan.id)
    messages.error(request, "Pesanan belum siap diambil.")
    return redirect('budget:status_pesanan')

# ==========================================
# 9. NOTIFIKASI
# ==========================================
@login_required
def notifikasi(request):
    notifs = Notifikasi.objects.filter(user=request.user).order_by('-waktu_kirim')
    unread_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
    Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).update(sudah_dibaca=True)
    try:
        role = request.user.profile.role
    except Exception:
        role = 'mahasiswa'

    ctx = {
        'notifs': notifs,
        'unread_count': unread_count,
        'notif_count': 0,
        'jumlah_keranjang': 0,
    }

    if role == 'admin':
        ctx['total_review_dilaporkan'] = ReviewMenu.objects.filter(dilaporkan=True).count()
    else:
        budget_data, _ = Budget.objects.get_or_create(user=request.user)
        ctx['budget'] = budget_data.saldo
        ctx['jumlah_keranjang'] = KeranjangItem.objects.filter(user=request.user).count()

    return render(request, 'budget/notifikasi.html', ctx)

@login_required
def tandai_baca(request, notif_id):
    notif = get_object_or_404(Notifikasi, id=notif_id, user=request.user)
    notif.sudah_dibaca = True
    notif.save()
    if (request.headers.get('x-requested-with') == 'XMLHttpRequest'
            or request.headers.get('Accept', '').startswith('application/json')
            or request.method == 'POST'):
        return JsonResponse({'ok': True, 'link': notif.link or '', 'judul': notif.judul})
    if notif.link:
        return redirect(notif.link)
    return redirect('budget:notifikasi')

# ==========================================
# 10. RIWAYAT & ANALITIK
# ==========================================
@login_required
def riwayat(request):
    pesanan_list = Pesanan.objects.filter(
        mahasiswa=request.user, status='selesai'
    ).order_by('-waktu_selesai')
    total_pengeluaran = pesanan_list.aggregate(total=Sum('total_harga'))['total'] or 0
    menu_favorit = ItemPesanan.objects.filter(
        pesanan__mahasiswa=request.user, pesanan__status='selesai'
    ).values('menu__nama_makanan', 'menu__id').annotate(
        total_pesan=Sum('jumlah')
    ).order_by('-total_pesan')[:5]
    pengeluaran_bulanan = Pesanan.objects.filter(
        mahasiswa=request.user, status='selesai', waktu_selesai__isnull=False,
    ).annotate(bulan=TruncMonth('waktu_selesai')).values('bulan').annotate(
        total=Sum('total_harga')
    ).order_by('bulan')
    pengeluaran_bulanan_json = json.dumps(
        [{'bulan': item['bulan'].isoformat(), 'total': item['total']} for item in pengeluaran_bulanan],
        cls=DjangoJSONEncoder
    )
    budget_data, _ = Budget.objects.get_or_create(user=request.user)
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
    jumlah_keranjang = KeranjangItem.objects.filter(user=request.user).count()
    return render(request, 'budget/riwayat.html', {
        'pesanan_list': pesanan_list, 'total_pengeluaran': total_pengeluaran,
        'menu_favorit': menu_favorit, 'pengeluaran_bulanan': pengeluaran_bulanan_json,
        'budget': budget_data.saldo, 'notif_count': notif_count,
        'jumlah_keranjang': jumlah_keranjang,
    })

# ==========================================
# 11. REVIEW MENU
# ==========================================
@login_required
def beri_review(request, pesanan_id):
    pesanan = get_object_or_404(Pesanan, id=pesanan_id, mahasiswa=request.user, status='selesai')
    items = pesanan.items.select_related('menu')
    budget_data, _ = Budget.objects.get_or_create(user=request.user)
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
    if request.method == 'POST':
        ada_review = False
        for item in items:
            bintang = request.POST.get(f'bintang_{item.menu.id}')
            komentar = request.POST.get(f'komentar_{item.menu.id}', '')
            if bintang:
                ReviewMenu.objects.update_or_create(
                    mahasiswa=request.user, menu=item.menu, pesanan=pesanan,
                    defaults={'bintang': int(bintang), 'komentar': komentar}
                )
                ada_review = True
        if ada_review:
            pesanan.sudah_direview = True
            pesanan.save()
            messages.success(request, "Terima kasih atas reviewmu!")
        return redirect('budget:riwayat')
    return render(request, 'budget/beri_review.html', {
        'pesanan': pesanan, 'items': items,
        'budget': budget_data.saldo, 'notif_count': notif_count,
    })

# ==========================================
# LAPORKAN REVIEW
# Hanya mahasiswa & pemilik yang bisa melaporkan.
# Admin tidak perlu laporkan — langsung kelola di halaman Moderasi.
# ==========================================
@login_required
def laporkan_review(request, review_id):
    try:
        role = request.user.profile.role
    except Exception:
        role = 'mahasiswa'

    if role == 'admin':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'msg': 'Admin tidak perlu melaporkan review.'}, status=403)
        messages.error(request, "Admin tidak perlu melaporkan review. Gunakan halaman Moderasi.")
        return redirect('budget:admin_moderasi')

    review = get_object_or_404(ReviewMenu, id=review_id)

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'msg': 'Method tidak diizinkan.'}, status=405)

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if not review.dilaporkan:
        review.dilaporkan = True
        review.save()

        # Notif ke semua admin (sudah ada sebelumnya, tidak diubah)
        notif_ke_semua_admin(
            "⚠️ Review Dilaporkan",
            f"Review menu '{review.menu.nama_makanan}' oleh {review.mahasiswa.username} "
            f"dilaporkan oleh {request.user.username}. Klik untuk moderasi.",
            tipe='sistem',
            link=reverse('budget:admin_moderasi')
        )

        # ── TAMBAHAN: Notif ke mahasiswa pelapor sebagai konfirmasi ──
        buat_notif(
            request.user,
            "Laporan Terkirim",
            f"Laporanmu untuk review menu '{review.menu.nama_makanan}' sudah diterima dan sedang ditinjau oleh admin.",
            tipe='sistem',
            link=reverse('budget:detail_menu', args=[review.menu.id])
        )

        if is_ajax:
            return JsonResponse({'status': 'ok'})
        messages.warning(request, "Review telah dilaporkan ke admin. Terima kasih!")
    else:
        if is_ajax:
            return JsonResponse({'status': 'already'})
        messages.info(request, "Review ini sudah pernah dilaporkan sebelumnya.")

    return redirect(request.META.get('HTTP_REFERER', '/'))

# ==========================================
# 12. PROFIL
# ==========================================
@login_required
def profil(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
    role = getattr(profile, 'role', 'mahasiswa')

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        profile.bio = request.POST.get('bio', '')
        profile.no_hp = request.POST.get('no_hp', '')
        if request.FILES.get('foto_profil'):
            profile.foto_profil = request.FILES['foto_profil']
        profile.save()
        messages.success(request, "Profil berhasil diperbarui!")
        return redirect('budget:profil')

    ctx = {
        'profile': profile,
        'notif_count': notif_count,
        'jumlah_keranjang': 0,
        'foto_profil_url': profile.foto_profil.url if (hasattr(profile, 'foto_profil') and profile.foto_profil) else None,
    }

    if role == 'admin':
        ctx['total_warung'] = Kantin.objects.count()
        ctx['total_pengguna'] = Profile.objects.filter(role='mahasiswa').count()
        ctx['total_review_dilaporkan'] = ReviewMenu.objects.filter(dilaporkan=True).count()
    elif role == 'pemilik':
        budget_data, _ = Budget.objects.get_or_create(user=request.user)
        ctx['budget'] = budget_data.saldo
        ctx['jumlah_keranjang'] = KeranjangItem.objects.filter(user=request.user).count()
        ctx['total_pesanan'] = Pesanan.objects.filter(warung__pemilik=request.user, status='selesai').count()
        ctx['total_pendapatan'] = Pesanan.objects.filter(
            warung__pemilik=request.user, status='selesai'
        ).aggregate(total=Sum('total_harga'))['total'] or 0
    else:
        budget_data, _ = Budget.objects.get_or_create(user=request.user)
        ctx['budget'] = budget_data.saldo
        ctx['jumlah_keranjang'] = KeranjangItem.objects.filter(user=request.user).count()
        ctx['total_pesanan'] = Pesanan.objects.filter(mahasiswa=request.user, status='selesai').count()
        ctx['total_pengeluaran'] = Pesanan.objects.filter(
            mahasiswa=request.user, status='selesai'
        ).aggregate(total=Sum('total_harga'))['total'] or 0

    return render(request, 'budget/profil.html', ctx)

@login_required
def ganti_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password', '')
        new_password1 = request.POST.get('new_password1', '')
        new_password2 = request.POST.get('new_password2', '')
        if not request.user.check_password(old_password):
            messages.error(request, "Password lama salah!")
        elif new_password1 != new_password2:
            messages.error(request, "Password baru tidak cocok!")
        elif len(new_password1) < 8:
            messages.error(request, "Password minimal 8 karakter!")
        else:
            request.user.set_password(new_password1)
            request.user.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            messages.success(request, "Password berhasil diubah!")
    return redirect('budget:profil')

# ==========================================
# 13. PILIH MENU LANGSUNG
# ==========================================
@login_required
def pilih_menu(request, menu_id):
    menu = get_object_or_404(Menu, id=menu_id)
    budget_data = get_object_or_404(Budget, user=request.user)

    try:
        jumlah = max(1, min(10, int(request.POST.get('jumlah', 1))))
    except (ValueError, TypeError):
        jumlah = 1

    total_bayar = menu.harga * jumlah

    if budget_data.saldo >= total_bayar:
        catatan_mhs = request.POST.get('catatan', '')
        budget_data.saldo -= total_bayar
        budget_data.save()
        pesanan = Pesanan.objects.create(
            mahasiswa=request.user, warung=menu.kantin,
            total_harga=total_bayar, status='pending', catatan=catatan_mhs
        )
        ItemPesanan.objects.create(
            pesanan=pesanan, menu=menu, jumlah=jumlah,
            harga_saat_pesan=menu.harga, catatan_item=catatan_mhs
        )
        menu.jumlah_terjual += jumlah
        menu.save()

        if menu.kantin.pemilik:
            buat_notif(
                menu.kantin.pemilik,
                "Ada Pesanan Baru!",
                f"{request.user.username} memesan {jumlah}x {menu.nama_makanan} — Pesanan #{pesanan.id}",
                tipe='pesanan',
                link=reverse('budget:detail_pesanan_pemilik', args=[pesanan.id])
            )

        buat_notif(
            request.user,
            "Pesanan Berhasil!",
            f"Pesanan {jumlah}x {menu.nama_makanan} (Rp {total_bayar:,}) sedang menunggu konfirmasi warung.",
            tipe='pesanan',
            link=f"{reverse('budget:status_pesanan')}?highlight={pesanan.id}"
        )

        notif_ke_semua_admin(
            "Pesanan Masuk Baru",
            f"{request.user.username} memesan {jumlah}x {menu.nama_makanan} di {menu.kantin.nama_kantin} — Pesanan #{pesanan.id}",
            tipe='pesanan',
            link=reverse('budget:admin_laporan')
        )

        messages.success(request, f"Pesanan {jumlah}x {menu.nama_makanan} berhasil dibuat!")
    else:
        kekurangan = total_bayar - budget_data.saldo
        messages.error(request, f"Budget tidak cukup! Kekurangan Rp {kekurangan:,}.")
    return redirect('budget:index')

# ==========================================
# 14. KANTIN DETAIL
# ==========================================
@login_required
def kantin_detail(request, kantin_id):
    return redirect('budget:katalog_menu', kantin_id=kantin_id)

# ==========================================
# 15. DASHBOARD WARUNG (PEMILIK)
# ==========================================
@login_required
def dashboard_warung(request):
    try:
        role = request.user.profile.role
    except Exception:
        role = None
    
    if role != 'pemilik':
        messages.error(request, "Akses dilarang!")
        return redirect('budget:index')  
    warung = Kantin.objects.filter(pemilik=request.user).first()
    if not warung:
        messages.warning(request, "Kamu belum memiliki warung. Hubungi admin.")
        return redirect('budget:index')
    pesanan_hari_ini = Pesanan.objects.filter(
        warung=warung, waktu_pesan__date=timezone.now().date()
    ).count()
    pesanan_pending = Pesanan.objects.filter(warung=warung, status='pending').count()
    pesanan_diproses = Pesanan.objects.filter(warung=warung, status='diproses').count()
    total_pendapatan_hari_ini = Pesanan.objects.filter(
        warung=warung, status='selesai', waktu_selesai__date=timezone.now().date()
    ).aggregate(total=Sum('total_harga'))['total'] or 0
    menu_terlaris = Menu.objects.filter(kantin=warung).order_by('-jumlah_terjual')[:5]
    pesanan_aktif = Pesanan.objects.filter(
        warung=warung, status__in=['pending', 'diproses']
    ).order_by('-waktu_pesan')[:5]
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
    return render(request, 'budget/dashboard_warung.html', {
        'warung': warung,
        'pesanan_hari_ini': pesanan_hari_ini,
        'pesanan_pending': pesanan_pending,
        'pesanan_diproses': pesanan_diproses,
        'total_pendapatan_hari_ini': total_pendapatan_hari_ini,
        'menu_terlaris': menu_terlaris,
        'pesanan_aktif': pesanan_aktif,
        'notif_count': notif_count,
        'pesanan_pending_count': get_pesanan_pending_count(request.user),  
    })

# ==========================================
# 16. KELOLA MENU (PEMILIK)
# ==========================================
@login_required
def manage_menu(request):
    if not is_pemilik(request.user):
        messages.error(request, "Akses dilarang!")
        return redirect('budget:index')
    warung = Kantin.objects.filter(pemilik=request.user).first()
    menus = Menu.objects.filter(kantin__pemilik=request.user)
    menu_id_aktif = request.GET.get('review_menu')
    reviews_menu = None
    menu_aktif = None
    if menu_id_aktif:
        menu_aktif = get_object_or_404(Menu, id=menu_id_aktif, kantin__pemilik=request.user)
        reviews_menu = ReviewMenu.objects.filter(menu=menu_aktif).select_related('mahasiswa').order_by('-waktu_review')
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
    return render(request, 'budget/manage_menu.html', {
        'menus': menus,
        'warung': warung,
        'notif_count': notif_count,
        'reviews_menu': reviews_menu,
        'menu_aktif': menu_aktif,
        'kategori_choices': Menu.KATEGORI_CHOICES,
        'pesanan_pending_count': get_pesanan_pending_count(request.user),  
    })

@login_required
def tambah_menu(request):
    if not is_pemilik(request.user):
        messages.error(request, "Akses dilarang!")
        return redirect('budget:index')
    warung = Kantin.objects.filter(pemilik=request.user).first()
    if request.method == 'POST':
        nama = request.POST.get('nama_makanan')
        harga = request.POST.get('harga')
        deskripsi = request.POST.get('deskripsi', '')
        label = request.POST.get('label', '')
        gambar = request.FILES.get('gambar')
        harga_clean = int(str(harga).replace('.', '').replace(',', '')) if harga else 0
        Menu.objects.create(
            nama_makanan=nama, harga=harga_clean, kantin=warung,
            deskripsi=deskripsi, label=label, gambar=gambar, stok_tersedia=True,
            kategori=request.POST.get('kategori', 'makanan')
        )
        messages.success(request, "Menu berhasil ditambahkan!")
        return redirect('budget:manage_menu')
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
    return render(request, 'budget/form_menu.html', {
        'title': 'Tambah Menu Baru', 
        'warung': warung, 
        'notif_count': notif_count,
        'kategori_choices': Menu.KATEGORI_CHOICES,
        'pesanan_pending_count': get_pesanan_pending_count(request.user), 
    })

@login_required
def edit_menu(request, menu_id):
    if not is_pemilik(request.user):
        messages.error(request, "Akses dilarang!")
        return redirect('budget:index')
    menu = get_object_or_404(Menu, id=menu_id, kantin__pemilik=request.user)
    if request.method == 'POST':
        menu.nama_makanan = request.POST.get('nama_makanan')
        harga_raw = request.POST.get('harga', '0').replace('.', '').replace(',', '')
        try:
            menu.harga = int(harga_raw)
        except ValueError:
            menu.harga = 0
        menu.deskripsi = request.POST.get('deskripsi', '')
        menu.label = request.POST.get('label', '')
        menu.kategori = request.POST.get('kategori', menu.kategori)
        menu.stok_tersedia = request.POST.get('stok_tersedia') == 'on'
        if request.FILES.get('gambar'):
            menu.gambar = request.FILES['gambar']
        menu.save()
        messages.success(request, "Menu berhasil diperbarui!")
        return redirect('budget:manage_menu')
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
    return render(request, 'budget/form_menu.html', {
        'title': 'Edit Menu',
        'menu': menu,
        'notif_count': notif_count,
        'kategori_choices': Menu.KATEGORI_CHOICES,
        'pesanan_pending_count': get_pesanan_pending_count(request.user),  # ← tambah ini
    })

@login_required
def hapus_menu(request, menu_id):
    if not is_pemilik(request.user):
        messages.error(request, "Akses dilarang!")
        return redirect('budget:index')
    menu = get_object_or_404(Menu, id=menu_id, kantin__pemilik=request.user)
    nama_menu = menu.nama_makanan
    nama_warung = menu.kantin.nama_kantin
    menu.delete()

    notif_ke_semua_admin(
        "Menu Dihapus",
        f"Menu '{nama_menu}' di warung '{nama_warung}' telah dihapus oleh pemilik.",
        tipe='sistem',
        link=reverse('budget:admin_kelola_warung')
    )

    messages.warning(request, "Menu dihapus.")
    return redirect('budget:manage_menu')

@login_required
def toggle_stok(request, menu_id):
    if not is_pemilik(request.user):
        return JsonResponse({'error': 'Akses dilarang'}, status=403)
    menu = get_object_or_404(Menu, id=menu_id, kantin__pemilik=request.user)
    menu.stok_tersedia = not menu.stok_tersedia
    menu.save()
    return JsonResponse({'stok': menu.stok_tersedia})

# ==========================================
# 17. KELOLA PESANAN (PEMILIK)
# ==========================================
@login_required
def kelola_pesanan(request):
    if not is_pemilik(request.user):
        messages.error(request, "Akses dilarang!")
        return redirect('budget:index')

    warung_saya = Kantin.objects.filter(pemilik=request.user).first()
    pesanan_masuk = Pesanan.objects.filter(
        warung__pemilik=request.user
    ).order_by('-waktu_pesan')

    now = timezone.now()
    for p in pesanan_masuk:
        if p.status in ['pending', 'diproses']:
            selisih = now - p.waktu_pesan
            p.menit_tunggu = int(selisih.total_seconds() // 60)
        else:
            p.menit_tunggu = 0

    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
    highlight_id = request.GET.get('highlight', '')

    return render(request, 'budget/kelola_pesanan.html', {
        'pesanan_masuk': pesanan_masuk,
        'warung': warung_saya,
        'notif_count': notif_count,
        'highlight_id': highlight_id,
        'pesanan_pending_count': get_pesanan_pending_count(request.user),  
    })

@login_required
def detail_pesanan_pemilik(request, pesanan_id):
    if not is_pemilik(request.user):
        messages.error(request, "Akses dilarang!")
        return redirect('budget:index')

    pesanan = get_object_or_404(Pesanan, id=pesanan_id, warung__pemilik=request.user)
    items = pesanan.items.select_related('menu').all()
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()

    now = timezone.now()
    if pesanan.status in ['pending', 'diproses']:
        selisih = now - pesanan.waktu_pesan
        pesanan.menit_tunggu = int(selisih.total_seconds() // 60)
    else:
        pesanan.menit_tunggu = 0

    return render(request, 'budget/detail_pesanan_pemilik.html', {
        'pesanan': pesanan,
        'items': items,
        'notif_count': notif_count,
        'pesanan_pending_count': get_pesanan_pending_count(request.user),
    })

# ==========================================
# 18. UPDATE STATUS PESANAN (PEMILIK)
# ==========================================
@login_required
def update_status_pesanan(request, pesanan_id):
    if not is_pemilik(request.user):
        messages.error(request, "Akses dilarang!")
        return redirect('budget:index')

    pesanan = get_object_or_404(Pesanan, id=pesanan_id, warung__pemilik=request.user)

    if request.method == 'POST':
        status_baru = request.POST.get('status')
        status_valid = ['pending', 'diproses', 'siap', 'selesai', 'dibatalkan']

        if status_baru in status_valid:
            pesanan.status = status_baru
            if status_baru == 'selesai':
                pesanan.waktu_selesai = timezone.now()
            pesanan.save()

            pesan_map = {
                'diproses':   f"Pesanan #{pesanan.id} sedang diproses oleh warung. Ditunggu ya!",
                'siap':       f"Pesanan #{pesanan.id} sudah siap! Silakan ambil ke warung sekarang.",
                'selesai':    f"Pesanan #{pesanan.id} telah selesai. Terima kasih sudah memesan!",
                'dibatalkan': f"Pesanan #{pesanan.id} dibatalkan oleh warung. Mohon maaf ya",
            }
            judul_map = {
                'diproses':   "Pesanan Sedang Diproses",
                'siap':       "Pesanan Siap Diambil!",
                'selesai':    "Pesanan Selesai",
                'dibatalkan': "Pesanan Dibatalkan",
            }

            if status_baru in pesan_map:
                buat_notif(
                    pesanan.mahasiswa,
                    judul_map[status_baru],
                    pesan_map[status_baru],
                    tipe='pesanan',
                    link=f"{reverse('budget:status_pesanan')}?highlight={pesanan.id}"
                )

            if status_baru == 'dibatalkan':
                notif_ke_semua_admin(
                    "Pesanan Dibatalkan",
                    f"Pesanan #{pesanan.id} milik {pesanan.mahasiswa.username} di '{pesanan.warung.nama_kantin}' dibatalkan oleh pemilik warung.",
                    tipe='pesanan',
                    link=reverse('budget:admin_laporan')
                )

            messages.success(request, f"Status pesanan #{pesanan.id} → '{pesanan.get_status_display()}'.")
        else:
            messages.error(request, "Status tidak valid.")

    from_detail = request.POST.get('from_detail', '')
    if from_detail:
        return redirect('budget:detail_pesanan_pemilik', pesanan_id=pesanan.id)
    return redirect(f"{reverse('budget:kelola_pesanan')}?highlight={pesanan.id}")

# ==========================================
# 19. PENGATURAN WARUNG (PEMILIK)
# ==========================================
@login_required
def pengaturan_warung(request):
    if not is_pemilik(request.user):
        messages.error(request, "Akses dilarang!")
        return redirect('budget:index')
 
    warung = Kantin.objects.filter(pemilik=request.user).first()
    if not warung:
        messages.error(request, "Kamu belum memiliki warung.")
        return redirect('budget:dashboard_warung')
 
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
 
    if request.method == 'POST':
        warung.nama_kantin = request.POST.get('nama_kantin', warung.nama_kantin)
        warung.lokasi = request.POST.get('lokasi', warung.lokasi)
        warung.jam_buka = request.POST.get('jam_buka', warung.jam_buka)
        warung.deskripsi = request.POST.get('deskripsi', warung.deskripsi)

        status_baru = request.POST.get('status_keramaian', warung.status_keramaian)
        warung.status_keramaian = status_baru
        warung.status_keramaian_updated_at = timezone.now()
 
        if request.FILES.get('foto_warung'):
            warung.foto_warung = request.FILES['foto_warung']
        warung.save()
        messages.success(request, "Pengaturan warung berhasil disimpan!")
        return redirect('budget:pengaturan_warung')
 
    return render(request, 'budget/pengaturan_warung.html', {
        'warung': warung,
        'notif_count': notif_count,
        'status_choices': Kantin.STATUS_KERAMAIAN,
        'pesanan_pending_count': get_pesanan_pending_count(request.user),
    })

# ==========================================
# 20. RIWAYAT & ANALITIK WARUNG (PEMILIK)
# ==========================================
@login_required
def riwayat_warung(request):
    try:
        kantin = Kantin.objects.get(pemilik=request.user)
    except Kantin.DoesNotExist:
        messages.error(request, "Kamu belum memiliki warung.")
        return redirect('budget:index')
 
    rentang_raw = request.GET.get('rentang', '7')
    try:
        rentang_hari = int(rentang_raw)
    except (ValueError, TypeError):
        rentang_hari = 7
 
    rentang = str(rentang_hari)
    tgl_mulai = timezone.now().date() - timedelta(days=rentang_hari - 1)
    from datetime import datetime
    tgl_mulai_dt = datetime.combine(tgl_mulai, datetime.min.time())
 
    pesanan_qs = Pesanan.objects.filter(
        warung=kantin,
        status='selesai',
        waktu_selesai__gte=tgl_mulai_dt,
    )
 
    total_pendapatan = pesanan_qs.aggregate(
        total=Coalesce(Sum('total_harga'), 0)
    )['total']
 
    total_pesanan = pesanan_qs.count()
 
    rata_per_pesanan = (total_pendapatan // total_pesanan) if total_pesanan > 0 else 0
 
    grafik_qs = (
        pesanan_qs
        .annotate(tgl=TruncDate('waktu_selesai'))
        .values('tgl')
        .annotate(pendapatan=Sum('total_harga'))
        .order_by('tgl')
    )
 
    pendapatan_by_tgl = {item['tgl']: item['pendapatan'] for item in grafik_qs}
    grafik_data = []
    for i in range(rentang_hari):
        tgl = tgl_mulai + timedelta(days=i)
        grafik_data.append({
            'tgl': tgl.strftime('%d/%m'),
            'pendapatan': pendapatan_by_tgl.get(tgl, 0),
        })
 
    grafik_json = json.dumps(grafik_data)
 
    menu_terlaris = (
        ItemPesanan.objects
        .filter(pesanan__in=pesanan_qs)
        .values('menu__nama_makanan')
        .annotate(
            total_terjual=Sum('jumlah'),
            total_pendapatan=Sum(
                ExpressionWrapper(
                    F('jumlah') * F('harga_saat_pesan'),
                    output_field=IntegerField()
                )
            ),
        )
        .order_by('-total_terjual')[:5]
    )
 
    riwayat_pesanan = (
        pesanan_qs
        .select_related('mahasiswa')
        .prefetch_related('items__menu')
        .order_by('-waktu_selesai')[:50]
    )
 
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
 
    return render(request, 'budget/riwayat_warung.html', {
        'kantin': kantin,
        'rentang': rentang,
        'tgl_mulai': tgl_mulai,
        'total_pendapatan': total_pendapatan,
        'total_pesanan': total_pesanan,
        'rata_per_pesanan': rata_per_pesanan,
        'grafik_json': grafik_json,
        'menu_terlaris': menu_terlaris,
        'riwayat_pesanan': riwayat_pesanan,
        'notif_count': notif_count,
    })

# ==========================================
# 21. ADMIN DASHBOARD
# ==========================================
@login_required
def admin_dashboard(request):
    if not is_admin(request.user):
        messages.error(request, "Akses dilarang!")
        return redirect('budget:index')

    total_warung              = Kantin.objects.count()
    total_mahasiswa           = Profile.objects.filter(role='mahasiswa').count()
    total_pemilik             = Profile.objects.filter(role='pemilik').count()
    total_pesanan_hari_ini    = Pesanan.objects.filter(waktu_pesan__date=timezone.now().date()).count()
    total_pesanan_semua       = Pesanan.objects.count()
    total_pesanan_pending     = Pesanan.objects.filter(status='pending').count()
    total_review_dilaporkan   = ReviewMenu.objects.filter(dilaporkan=True).count()
    total_pendapatan          = Pesanan.objects.filter(status='selesai').aggregate(total=Sum('total_harga'))['total'] or 0

    tgl_mulai = timezone.now().date() - timedelta(days=6)
    grafik_pesanan = (
        Pesanan.objects.filter(waktu_pesan__date__gte=tgl_mulai)
        .annotate(tgl=TruncDate('waktu_pesan'))
        .values('tgl').annotate(jumlah=Count('id')).order_by('tgl')
    )
    grafik_json = json.dumps(
        [{'tgl': str(p['tgl']), 'jumlah': p['jumlah']} for p in grafik_pesanan],
        cls=DjangoJSONEncoder
    )

    semua_warung = Kantin.objects.select_related('pemilik__profile').annotate(
        total_pesanan=Count('pesanan')
    ).order_by('-total_pesanan')

    warung_aktif = semua_warung[:5]
    pesanan_terbaru = Pesanan.objects.select_related('mahasiswa', 'warung').order_by('-waktu_pesan')[:10]
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()

    return render(request, 'budget/admin_dashboard.html', {
        'total_warung': total_warung,
        'total_mahasiswa': total_mahasiswa,
        'total_pemilik': total_pemilik,
        'total_pesanan_hari_ini': total_pesanan_hari_ini,
        'total_pesanan_semua': total_pesanan_semua,
        'total_pesanan_pending': total_pesanan_pending,
        'total_review_dilaporkan': total_review_dilaporkan,
        'total_pendapatan': total_pendapatan,
        'grafik_json': grafik_json,
        'semua_warung': semua_warung,
        'warung_aktif': warung_aktif,
        'pesanan_terbaru': pesanan_terbaru,
        'notif_count': notif_count,
    })

# ==========================================
# 22. ADMIN KELOLA WARUNG
# ==========================================
@login_required
def admin_kelola_warung(request):
    if not is_admin(request.user):
        messages.error(request, "Akses dilarang!")
        return redirect('budget:index')
 
    if request.method == 'POST':
        aksi = request.POST.get('aksi', '')
 
        if aksi == 'tambah_warung':
            nama = request.POST.get('nama_kantin', '').strip()
            lokasi = request.POST.get('lokasi', '').strip()
            jam_buka = request.POST.get('jam_buka', '').strip()
            username_pemilik = request.POST.get('username_pemilik', '').strip()
            password_pemilik = request.POST.get('password_pemilik', '').strip()
 
            if not nama:
                messages.error(request, "Nama warung wajib diisi.")
                return redirect('budget:admin_kelola_warung')
            if not username_pemilik or not password_pemilik:
                messages.error(request, "Username dan password pemilik wajib diisi.")
                return redirect('budget:admin_kelola_warung')
            if User.objects.filter(username=username_pemilik).exists():
                messages.error(request, f"Username '{username_pemilik}' sudah digunakan.")
                return redirect('budget:admin_kelola_warung')
 
            pemilik_user = User.objects.create_user(
                username=username_pemilik,
                password=password_pemilik,
            )
            profile_obj, _ = Profile.objects.get_or_create(user=pemilik_user)
            profile_obj.role = 'pemilik'
            profile_obj.save()
            Budget.objects.get_or_create(user=pemilik_user, defaults={'saldo': 0})
 
            kantin = Kantin(nama_kantin=nama, lokasi=lokasi, jam_buka=jam_buka, pemilik=pemilik_user)
            if request.FILES.get('foto_warung'):
                kantin.foto_warung = request.FILES['foto_warung']
            kantin.save()
 
            buat_notif(
                pemilik_user,
                "Selamat Datang!",
                f"Akun pemilik warung '{nama}' berhasil dibuat oleh admin. Login dengan username: {username_pemilik}",
                tipe='sistem'
            )
            messages.success(request, f"Warung '{nama}' dan akun pemilik '{username_pemilik}' berhasil ditambahkan!")
            return redirect('budget:admin_kelola_warung')
 
        elif aksi == 'hapus_warung':
            kantin = get_object_or_404(Kantin, id=request.POST.get('warung_id'))
            nama = kantin.nama_kantin
            kantin.delete()
            messages.warning(request, f"Warung '{nama}' berhasil dihapus.")
            return redirect('budget:admin_kelola_warung')
 
        elif aksi == 'aktifkan':
            kantin = get_object_or_404(Kantin, id=request.POST.get('warung_id'))
            kantin.status_keramaian = 'Normal'
            if hasattr(kantin, 'status_keramaian_updated_at'):
                kantin.status_keramaian_updated_at = timezone.now()
            kantin.save()
            messages.success(request, f"Warung '{kantin.nama_kantin}' diaktifkan.")
            return redirect('budget:admin_kelola_warung')
 
        elif aksi == 'nonaktifkan':
            kantin = get_object_or_404(Kantin, id=request.POST.get('warung_id'))
            kantin.status_keramaian = 'Sepi'
            if hasattr(kantin, 'status_keramaian_updated_at'):
                kantin.status_keramaian_updated_at = timezone.now()
            kantin.save()
            messages.warning(request, f"Warung '{kantin.nama_kantin}' dinonaktifkan.")
            return redirect('budget:admin_kelola_warung')
 
        else:
            messages.error(request, "Aksi tidak dikenali.")
            return redirect('budget:admin_kelola_warung')
 
    warung_list = Kantin.objects.all().select_related('pemilik__profile').annotate(
        total_menu=Count('menus', distinct=True),
        total_pesanan=Count(
            'pesanan',
            filter=Q(pesanan__status='selesai'),
            distinct=True,
        ),
    )
 
    pemilik_list = Profile.objects.filter(role='pemilik').select_related('user').prefetch_related(
        'user__warung'
    )
    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()
 
    return render(request, 'budget/admin_kelola_warung.html', {
        'warung_list': warung_list,
        'pemilik_list': pemilik_list,
        'notif_count': notif_count,
    })

# ==========================================
# 23. ADMIN LAPORAN
# ==========================================
@login_required
def admin_laporan(request):
    if not is_admin(request.user):
        messages.error(request, "Akses dilarang!")
        return redirect('budget:index')

    rentang = request.GET.get('rentang', '30')
    try:
        hari = int(rentang)
        if hari < 1:
            hari = 30
    except ValueError:
        hari = 30
        rentang = '30'

    tgl_mulai = timezone.now().date() - timedelta(days=hari - 1)
    pesanan_selesai = Pesanan.objects.filter(status='selesai', waktu_pesan__date__gte=tgl_mulai)

    total_pendapatan      = pesanan_selesai.aggregate(total=Sum('total_harga'))['total'] or 0
    total_pesanan         = Pesanan.objects.filter(waktu_pesan__date__gte=tgl_mulai).count()
    total_pesanan_selesai = pesanan_selesai.count()
    total_pesanan_pending = Pesanan.objects.filter(status='pending', waktu_pesan__date__gte=tgl_mulai).count()
    total_pengguna_aktif  = Pesanan.objects.filter(
        waktu_pesan__date__gte=tgl_mulai
    ).values('mahasiswa').distinct().count()
    rata_nilai_pesanan = (total_pendapatan / total_pesanan_selesai) if total_pesanan_selesai > 0 else 0

    pesanan_per_warung = Kantin.objects.annotate(
        jumlah_pesanan=Count('pesanan', filter=Q(pesanan__waktu_pesan__date__gte=tgl_mulai)),
        total_omzet=Sum('pesanan__total_harga', filter=Q(
                pesanan__status='selesai', pesanan__waktu_pesan__date__gte=tgl_mulai
        ))
    ).order_by('-total_omzet')

    grafik_bulanan = (
        pesanan_selesai.annotate(bln=TruncMonth('waktu_pesan'))
        .values('bln').annotate(total=Sum('total_harga'), jumlah=Count('id')).order_by('bln')
    )
    BULAN_ID = ['','Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agt','Sep','Okt','Nov','Des']
    grafik_json = json.dumps(
        [{'bulan': BULAN_ID[p['bln'].month] + ' ' + str(p['bln'].year), 'total': p['total'] or 0}
         for p in grafik_bulanan],
        cls=DjangoJSONEncoder
    )

    menu_populer = (
        ItemPesanan.objects.filter(pesanan__waktu_pesan__date__gte=tgl_mulai)
        .values('menu__nama_makanan', 'menu__kantin__nama_kantin')
        .annotate(total_terjual=Sum('jumlah'))
        .order_by('-total_terjual')[:10]
    )

    warung_ramai = (
        Pesanan.objects.filter(waktu_pesan__date__gte=tgl_mulai)
        .values('warung__nama_kantin')
        .annotate(
            total_pesanan=Count('id'),
            total_pendapatan=Sum('total_harga', filter=Q(status='selesai'))
        )
        .order_by('-total_pesanan')[:10]
    )
    warung_ramai_json = json.dumps(
        [{'nama': w['warung__nama_kantin'], 'pesanan': w['total_pesanan']} for w in warung_ramai],
        cls=DjangoJSONEncoder
    )

    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()

    return render(request, 'budget/admin_laporan.html', {
        'total_transaksi': total_pendapatan,
        'total_pesanan_selesai': total_pesanan_selesai,
        'total_pesanan_pending': total_pesanan_pending,
        'rata_nilai_pesanan': rata_nilai_pesanan,
        'total_pengguna_aktif': total_pengguna_aktif,
        'menu_populer': menu_populer,
        'warung_ramai': warung_ramai,
        'pesanan_per_warung': pesanan_per_warung,
        'transaksi_json': grafik_json,
        'warung_ramai_json': warung_ramai_json,
        'rentang': rentang,
        'tgl_mulai': tgl_mulai,
        'notif_count': notif_count,
    })

# ==========================================
# 24. ADMIN MODERASI REVIEW
# ==========================================
@login_required
def admin_moderasi(request):
    if not is_admin(request.user):
        messages.error(request, "Akses dilarang!")
        return redirect('budget:index')

    if request.method == 'POST':
        review = get_object_or_404(ReviewMenu, id=request.POST.get('review_id'))
        aksi = request.POST.get('aksi')

        if aksi == 'hapus':
            nama = review.menu.nama_makanan
            review.delete()
            messages.success(request, f"Review untuk '{nama}' berhasil dihapus permanen.")

        elif aksi == 'laporkan':
            # Admin menandai review sebagai perlu moderasi (set dilaporkan=True)
            if not review.dilaporkan:
                review.dilaporkan = True
                review.save()
                messages.warning(request, "Review berhasil ditandai sebagai perlu moderasi.")
            else:
                messages.info(request, "Review ini sudah ditandai sebelumnya.")

        elif aksi == 'tandai':
            # Tandai aman: review sudah ditinjau, bukan pelanggaran
            review.dilaporkan = False
            review.save()
            messages.success(request, "Review berhasil ditandai aman.")

        elif aksi == 'abaikan':
            # Abaikan laporan: sama dengan tandai aman tapi dari tab dilaporkan
            review.dilaporkan = False
            review.save()
            messages.info(request, "Laporan diabaikan. Review tetap tampil di sistem.")

        return redirect('budget:admin_moderasi')

    reviews_dilaporkan = ReviewMenu.objects.filter(
        dilaporkan=True
    ).select_related('mahasiswa', 'menu__kantin').order_by('-waktu_review')

    semua_review = ReviewMenu.objects.all().select_related(
        'mahasiswa', 'menu__kantin'
    ).order_by('-waktu_review')[:50]

    notif_count = Notifikasi.objects.filter(user=request.user, sudah_dibaca=False).count()

    tab = request.GET.get('tab', 'dilaporkan')
    if tab == 'semua':
        reviews = semua_review
    else:
        reviews = reviews_dilaporkan
        tab = 'dilaporkan'

    total_dilaporkan   = ReviewMenu.objects.filter(dilaporkan=True).count()
    total_semua_review = ReviewMenu.objects.count()

    return render(request, 'budget/admin_moderasi.html', {
        'reviews': reviews,
        'reviews_dilaporkan': reviews_dilaporkan,
        'semua_review': semua_review,
        'tab': tab,
        'total_dilaporkan': total_dilaporkan,
        'total_semua_review': total_semua_review,
        'notif_count': notif_count,
    })