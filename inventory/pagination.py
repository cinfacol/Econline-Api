from rest_framework.pagination import PageNumberPagination


class InventoryPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    page_size_query_description = "Número de elementos por página (predeterminado: 12)"
