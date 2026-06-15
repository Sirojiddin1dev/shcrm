from django.db import migrations, models
from django.utils import timezone


def mark_existing_linked_customers_verified(apps, schema_editor):
    Customer = apps.get_model('customers', 'Customer')
    Customer.objects.exclude(telegram_chat_id='').filter(
        telegram_verified_at__isnull=True,
    ).update(telegram_verified_at=timezone.now())


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0003_fix_debtor_status_when_zero_debt'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='telegram_verified_at',
            field=models.DateTimeField(
                blank=True, null=True, verbose_name='Telegram tasdiqlangan vaqti'
            ),
        ),
        migrations.RunPython(
            mark_existing_linked_customers_verified,
            migrations.RunPython.noop,
        ),
    ]
