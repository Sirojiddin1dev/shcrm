from django.db import migrations


def forwards(apps, schema_editor):
    """Mavjud mahsulot ma'lumotlarini 'Asosiy' variantga ko'chirish.

    - Variantsiz har bir mahsulot uchun uning narx/miqdor/valyuta/birligini
      saqlagan 'Asosiy' variant yaratiladi.
    - Avval qo'shilgan variantlarga mahsulotning valyuta/birlik/chegarasi ko'chiriladi.
    - Variantga bog'lanmagan eski sotuv/harid bandlari shu mahsulotning
      birinchi (asosiy) variantiga bog'lanadi.
    """
    Product = apps.get_model('products', 'Product')
    ProductVariant = apps.get_model('products', 'ProductVariant')
    SaleItem = apps.get_model('sales', 'SaleItem')
    PurchaseItem = apps.get_model('purchases', 'PurchaseItem')

    default_variant_by_product = {}

    for product in Product.objects.all():
        variants = list(product.variants.all())

        if variants:
            # Eski variantlar mahsulot narxini "meros" qilardi — endi o'ziga ko'chiramiz
            for v in variants:
                changed = False
                if not v.cost_price:
                    v.cost_price = product.cost_price
                    changed = True
                if not v.sale_price:
                    v.sale_price = product.sale_price
                    changed = True
                # currency/unit/threshold default qiymatda bo'lsa — mahsulotnikini olamiz
                if v.currency == 'uzs' and product.currency != 'uzs':
                    v.currency = product.currency
                    changed = True
                if v.unit == 'dona' and product.unit != 'dona':
                    v.unit = product.unit
                    changed = True
                if v.low_stock_threshold == 5 and product.low_stock_threshold != 5:
                    v.low_stock_threshold = product.low_stock_threshold
                    changed = True
                if changed:
                    v.save()
            default = next((v for v in variants if v.is_active), variants[0])
        else:
            default = ProductVariant.objects.create(
                product=product,
                name='Asosiy',
                barcode=product.barcode or '',
                cost_price=product.cost_price,
                sale_price=product.sale_price,
                currency=product.currency,
                quantity=product.quantity,
                unit=product.unit,
                low_stock_threshold=product.low_stock_threshold,
                is_active=True,
            )

        default_variant_by_product[product.id] = default.id

    # Variantsiz qolgan eski bandlarni asosiy variantga bog'lash
    for item in SaleItem.objects.filter(variant__isnull=True):
        vid = default_variant_by_product.get(item.product_id)
        if vid:
            item.variant_id = vid
            item.save(update_fields=['variant'])

    for item in PurchaseItem.objects.filter(variant__isnull=True):
        vid = default_variant_by_product.get(item.product_id)
        if vid:
            item.variant_id = vid
            item.save(update_fields=['variant'])


def backwards(apps, schema_editor):
    # Ma'lumotni qaytarish: asosiy variant qiymatlarini mahsulotga yozish
    Product = apps.get_model('products', 'Product')
    for product in Product.objects.all():
        v = product.variants.filter(is_active=True).first() or product.variants.first()
        if v:
            product.cost_price = v.cost_price
            product.sale_price = v.sale_price
            product.currency = v.currency
            product.quantity = v.quantity
            product.unit = v.unit
            product.low_stock_threshold = v.low_stock_threshold
            if not product.barcode:
                product.barcode = v.barcode
            product.save()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_productvariant_currency_and_more'),
        ('sales', '0008_saleitem_variant'),
        ('purchases', '0004_purchaseitem_variant'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
