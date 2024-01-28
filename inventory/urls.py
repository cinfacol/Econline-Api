from django.urls import path

from .views import (
    CategoryList,
    ProductByCategory,
    InventoryList,
    InventoryByRefCode,
)

urlpatterns = [
    path("all/", InventoryList.as_view()),
    path("category/all/", CategoryList.as_view()),
    path(
        "category/<str:query>/",
        ProductByCategory.as_view(),
    ),
    path("<str:query>/", InventoryByRefCode.as_view()),
]
