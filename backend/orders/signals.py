from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Delivery, OrderItem


@receiver(post_save, sender=OrderItem, dispatch_uid="orders_create_delivery")
def create_delivery_for_order_item(sender, instance, created, raw=False, **kwargs):
    if not created or raw:
        return
    order = instance.order
    Delivery.objects.create(
        order_item=instance,
        customer=order.user,
        product=instance.product,
        quantity=instance.quantity,
        total_price=instance.total_price,
        delivery_address=order.address,
    )
