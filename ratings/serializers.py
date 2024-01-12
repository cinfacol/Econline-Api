from rest_framework import serializers

from .models import Rating


class RatingSerializer(serializers.ModelSerializer):
    rater = serializers.StringRelatedField(read_only=True)
    product = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Rating
        fields = ["id", "rating", "comment"]

    def get_rater(self, obj):
        return obj.rater.username

    def get_product(self, obj):
        return obj.product.title
