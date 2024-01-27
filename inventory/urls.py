from django.urls import path

from .views import (
    CategoryList,
    ProductByCategory,
    InventoryByUpc,
)

urlpatterns = [
    path("category/all/", CategoryList.as_view()),
    path(
        "products/category/<str:query>/",
        ProductByCategory.as_view(),
    ),
    path("<int:query>/", InventoryByUpc.as_view()),
]
