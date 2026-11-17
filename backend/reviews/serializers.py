from rest_framework import serializers


class RatingInputSerializer(serializers.Serializer):
    """Body of PUT /api/products/{id}/my-rating/  ->  {"score": 1..5}"""

    score = serializers.IntegerField(min_value=1, max_value=5)