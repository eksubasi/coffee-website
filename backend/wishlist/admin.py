from django.contrib import admin

from .models import WishlistItem


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "created_at"]
    list_select_related = ["user", "product"]
    raw_id_fields = ["user", "product"]
