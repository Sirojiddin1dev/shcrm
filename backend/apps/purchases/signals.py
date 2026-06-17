from django.db.models import F
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from apps.products.models import ProductVariant
from .models import PurchaseItem


@receiver(pre_delete, sender=PurchaseItem)
def restore_stock_on_purchase_item_delete(sender, instance, **kwargs):
    """Harid (yoki uning bandi) o'chirilganda, harid yaratishda qo'shilgan
    miqdorni variant qoldig'idan qaytarib ayiradi. Purchase o'chganda
    PurchaseItem'lar cascade bilan o'chadi va bu signal har biri uchun ishlaydi —
    shu sabab API va admin paneldan o'chirishni ham qamrab oladi."""
    if instance.variant_id:
        ProductVariant.objects.filter(pk=instance.variant_id).update(
            quantity=F('quantity') - instance.quantity
        )
