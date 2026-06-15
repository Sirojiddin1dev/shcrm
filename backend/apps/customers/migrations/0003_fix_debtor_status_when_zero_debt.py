from django.db import migrations


def fix_debtor_status(apps, schema_editor):
    Customer = apps.get_model('customers', 'Customer')
    to_fix = Customer.objects.filter(status='debtor', debt_uzs=0, debt_usd=0)
    fixed = 0
    for c in to_fix:
        c.status = 'vip' if c.total_spent_uzs >= 1_000_000 else 'active'
        c.save(update_fields=['status'])
        fixed += 1
    if fixed:
        print(f"\n  {fixed} ta mijoz statusi tuzatildi (debtor -> active/vip)")


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0002_remove_customer_debt_remove_customer_total_spent_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_debtor_status, migrations.RunPython.noop),
    ]
