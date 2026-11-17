from django.contrib import admin

from .models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ["product", "user", "score", "updated_at"]
    list_filter = ["score"]