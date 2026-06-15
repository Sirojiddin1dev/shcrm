from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0006_remove_sale_currency_sale_total_usd_sale_total_uzs_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='debt_due_5_days_reminded_at',
            field=models.DateTimeField(
                blank=True, null=True, verbose_name='5 kun oldin eslatma yuborilgan vaqt'
            ),
        ),
        migrations.AddField(
            model_name='sale',
            name='debt_due_today_reminded_at',
            field=models.DateTimeField(
                blank=True, null=True, verbose_name='Muddat kuni eslatma yuborilgan vaqt'
            ),
        ),
    ]
