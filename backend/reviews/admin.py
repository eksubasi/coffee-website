from django.contrib import admin

from .models import Comment, Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ["product", "user", "score", "updated_at"]
    list_filter = ["score"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["product", "user", "status", "created_at", "reviewed_by"]
    list_filter = ["status"]
    search_fields = ["text", "user__email", "product__name"]