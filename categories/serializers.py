from rest_framework import serializers
from .models import Category


""" class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "parent",
            "name",
        ] """


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        exclude = ["updated_at"]
        depth = 1
