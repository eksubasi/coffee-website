"""
KAN-71: python manage.py demo_reset [--yes]

Puts the database into a known state before a demo, so the progress demo
never needs manual database fixes:

1. Reseeds the catalog from the product spreadsheet (stock back to the
   spreadsheet values).
2. Creates or resets one demo account per role (password: DEMO_PASSWORD,
   default "brewnook-demo") and clears their orders, carts, ratings,
   comments, wishlists and chats.
3. Deletes accounts registered during an earlier demo, i.e. every email
   ending in "@demo.brewnook.dev".
4. Creates one delivered order for the demo customer, so rating and
   commenting can be shown live.

Safe to run repeatedly. Outside DEBUG it refuses to run unless --yes is given.
"""

import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.management.commands.seed_users import DEFAULT_DEMO_PASSWORD, demo_users
from cart.models import Cart, CartItem
from catalog.models import Product
from chat.models import Conversation, Message
from invoices.models import Invoice
from orders.checkout import checkout
from orders.models import Order
from orders.services import change_order_status
from payments.cards import card_token
from payments.models import PaymentToken
from reviews.models import Comment, Rating
from wishlist.models import WishlistItem

# Accounts created by registering during a demo use this email domain.
DEMO_SIGNUP_DOMAIN = "@demo.brewnook.dev"

# The product in the demo customer's delivered order (rated and commented live).
DELIVERED_PRODUCT_MODEL = "DB-ETH-250"
DEMO_ADDRESS = "Orta Mahalle, Universite Caddesi No:27, Tuzla, Istanbul"
DEMO_TAX_ID = "1234567890"
DEMO_CARD = "4111111111111111"


def clear_user_data(users):
    """Remove everything these users created, in an order PROTECT allows."""
    Invoice.objects.filter(order__user__in=users).delete()
    Order.objects.filter(user__in=users).delete()  # items and deliveries cascade
    Message.objects.filter(sender__in=users).delete()
    Message.objects.filter(conversation__user__in=users).delete()
    Conversation.objects.filter(user__in=users).delete()
    CartItem.objects.filter(cart__user__in=users).delete()
    Rating.objects.filter(user__in=users).delete()
    Comment.objects.filter(user__in=users).delete()
    WishlistItem.objects.filter(user__in=users).delete()
    PaymentToken.objects.filter(user__in=users).delete()


class Command(BaseCommand):
    help = "Reset the database to the progress-demo starting state (KAN-71)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Required when DEBUG is off (e.g. on the deployed database).",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["yes"]:
            raise CommandError(
                "DEBUG is off: this would reset the demo data on a real database. "
                "Run again with --yes if that is what you want."
            )

        User = get_user_model()
        password = os.environ.get("DEMO_PASSWORD") or DEFAULT_DEMO_PASSWORD

        with transaction.atomic():
            call_command("seed_catalog", stdout=self.stdout)

            signups = User.objects.filter(email__iendswith=DEMO_SIGNUP_DOMAIN)
            removed = signups.count()
            clear_user_data(signups)
            signups.delete()

            role_users = []
            for email, full_name, role in demo_users():
                user, _ = User.objects.get_or_create(email=email, defaults={"role": role})
                user.full_name = full_name
                user.role = role
                user.is_active = True
                user.set_password(password)
                if role == User.Role.CUSTOMER:
                    user.home_address = DEMO_ADDRESS
                    user.tax_id = DEMO_TAX_ID
                user.save()
                role_users.append(user)
            clear_user_data(role_users)

            customer = next(u for u in role_users if u.role == User.Role.CUSTOMER)
            order = self._create_delivered_order(customer)

        self.stdout.write(f"Removed {removed} account(s) registered during earlier demos.")
        for user in role_users:
            self.stdout.write(f"Demo account: {user.email} ({user.role})")
        self.stdout.write(
            f"Delivered order #{order.pk} for {customer.email}: "
            f"{order.items.first().product.name}"
        )
        self.stdout.write(self.style.SUCCESS("Demo data is ready."))

    def _create_delivered_order(self, customer):
        product = Product.objects.filter(model=DELIVERED_PRODUCT_MODEL).first()
        if product is None or product.quantity_in_stock < 1:
            raise CommandError(f"Product {DELIVERED_PRODUCT_MODEL} is missing or out of stock.")

        cart, _ = Cart.objects.get_or_create(user=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        token, _ = PaymentToken.objects.get_or_create(
            user=customer,
            token=card_token(DEMO_CARD),
            defaults={"last4": DEMO_CARD[-4:]},
        )
        order = checkout(customer, DEMO_ADDRESS, token)
        return change_order_status(order.pk, Order.Status.DELIVERED)