from rest_framework import serializers
from .models import Category, MeasureUnit


class MeasureUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasureUnit
        fields = ("id", "description")


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "parent", "is_active", "measure_unit")
        depth = 1
