from rest_framework import serializers

from .models import Rating


class RatingSerializer(serializers.ModelSerializer):
    rater = serializers.SerializerMethodField(read_only=True)
    product = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Rating
        fields = ["id", "rater", "product", "rating", "comment", "created_at"]

    def get_rater(self, obj):
        return obj.rater.username

    def get_product(self, obj):
        return obj.product.title

    def create(self, validated_data):
        product_id = self.context["product_id"]
        user_id = self.context["rater_id"]
        rating = Rating.objects.create(
            product_id=product_id, rater_id=user_id, **self.validated_data
        )
        return rating
