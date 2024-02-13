from django.urls import path

from .views import (
    InventoryByCategory,
    InventoryListAPIView,
    ListUsersInventoryAPIView,
    InventoryDetailView,
    InventoryByRefCode,
    InventorySearchAPIView,
    update_inventory_api_view,
    create_inventory_api_view,
    delete_inventory_api_view,
)

urlpatterns = [
    path("all/", InventoryListAPIView.as_view()),
    path("users/", ListUsersInventoryAPIView.as_view(), name="user-inventories"),
    path(
        "details/<int:sku>/",
        InventoryDetailView.as_view(),
        name="inventory-details",
    ),
    path(
        "category/<str:query>/",
        InventoryByCategory.as_view(),
    ),
    path("<str:query>/", InventoryByRefCode.as_view()),
    path("update/<int:sku>/", update_inventory_api_view, name="update-inventory"),
    path("create/", create_inventory_api_view, name="inventory-create"),
    path("delete/<int:sku>/", delete_inventory_api_view, name="delete-inventory"),
    path("search/", InventorySearchAPIView.as_view(), name="inventory-search"),
]
