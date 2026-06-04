from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0004_kantin_status_keramaian_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='menu',
            name='kategori',
            field=models.CharField(
                choices=[
                    ('makanan', 'Makanan'),
                    ('minuman', 'Minuman'),
                    ('snack', 'Snack'),
                    ('paket', 'Paket'),
                    ('lainnya', 'Lainnya'),
                ],
                default='makanan',
                max_length=20,
            ),
        ),
    ]