from rest_framework import permissions, status, generics
from rest_framework.response import Response

# from rest_framework.views import APIView

from .models import Category
from .serializers import CategorySerializer


class ListCategoriesView(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrar por query params (modificado)
        name = self.request.query_params.get("name", None)
        is_active = self.request.query_params.get("is_active", None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        if is_active is not None:
            # Use boolean conversion to handle different truthy values
            queryset = queryset.filter(is_active=bool(is_active))
        return queryset
