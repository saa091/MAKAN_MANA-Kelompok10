from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Tambah field baru ke Profile
        migrations.AddField(
            model_name='profile',
            name='bio',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='no_hp',
            field=models.CharField(blank=True, max_length=20),
        ),

        # Tambah field ke Kantin
        migrations.AddField(
            model_name='kantin',
            name='deskripsi',
            field=models.TextField(blank=True),
        ),

        # Tambah field ke Pesanan
        migrations.AddField(
            model_name='pesanan',
            name='sudah_direview',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='pesanan',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('diproses', 'Diproses'),
                    ('siap', 'Siap Diambil'),
                    ('selesai', 'Selesai'),
                    ('dibatalkan', 'Dibatalkan'),
                ],
                default='pending', max_length=20,
            ),
        ),

        # Tambah field ke ReviewMenu
        migrations.AddField(
            model_name='reviewmenu',
            name='dilaporkan',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='reviewmenu',
            name='pesanan',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='budget.pesanan',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='reviewmenu',
            unique_together={('mahasiswa', 'menu', 'pesanan')},
        ),

        # Tambah field ke Notifikasi
        migrations.AddField(
            model_name='notifikasi',
            name='tipe',
            field=models.CharField(
                choices=[('pesanan','Pesanan'),('budget','Budget'),('review','Review'),('sistem','Sistem')],
                default='sistem', max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='notifikasi',
            name='link',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterModelOptions(
            name='notifikasi',
            options={'ordering': ['-waktu_kirim']},
        ),

        # Buat model KeranjangItem
        migrations.CreateModel(
            name='KeranjangItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jumlah', models.IntegerField(default=1)),
                ('catatan_item', models.TextField(blank=True)),
                ('ditambahkan', models.DateTimeField(auto_now_add=True)),
                ('menu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='budget.menu')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='keranjang',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'unique_together': {('user', 'menu')}},
        ),
    ]