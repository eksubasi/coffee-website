from rest_framework import serializers

from .models import Comment

COMMENT_MAX_LENGTH = 1000


class RatingInputSerializer(serializers.Serializer):
    """Body of PUT /api/products/{id}/my-rating/  ->  {"score": 1..5}"""

    score = serializers.IntegerField(min_value=1, max_value=5)


def public_author_name(user):
    """'Melike Yildirim' -> 'Melike Y.'; customers without a name -> 'Customer'.

    The email address is never shown to other visitors.
    """
    parts = (user.full_name or "").split()
    if not parts:
        return "Customer"
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} {parts[-1][0]}."


class CommentInputSerializer(serializers.Serializer):
    """Body of POST /api/products/{id}/comments/  ->  {"text": "..."}"""

    text = serializers.CharField(max_length=COMMENT_MAX_LENGTH, trim_whitespace=True)


class PublicCommentSerializer(serializers.ModelSerializer):
    """What every visitor sees under a product: approved comments only."""

    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "author", "text", "created_at"]
        read_only_fields = fields

    def get_author(self, comment):
        return public_author_name(comment.user)


class MyCommentSerializer(serializers.ModelSerializer):
    """The customer's own comments, with their status ("pending" notice in the UI)."""

    class Meta:
        model = Comment
        fields = ["id", "product", "text", "status", "created_at"]
        read_only_fields = fields


class ModerationCommentSerializer(serializers.ModelSerializer):
    """What a product manager sees in the moderation queue (KAN-61)."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    customer_email = serializers.EmailField(source="user.email", read_only=True)
    reviewed_by_email = serializers.EmailField(
        source="reviewed_by.email", read_only=True, default=None
    )

    class Meta:
        model = Comment
        fields = [
            "id",
            "product",
            "product_name",
            "customer_email",
            "text",
            "status",
            "created_at",
            "reviewed_by_email",
            "reviewed_at",
        ]
        read_only_fields = fields