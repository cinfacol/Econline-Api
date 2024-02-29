from rest_framework import serializers

from .models import Product

# from reviews.models import Review

# from categories.serializers import CategorySerializer


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "ref_code",
            "category",
            "description",
        ]
        read_only = True
        editable = False
        depth = 2
