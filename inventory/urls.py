from django.urls import path

from .views import (
    InventoryByCategoryAPIView,
    InventoryListAPIView,
    ListUsersInventoryAPIView,
    InventoryDetailView,
    InventoryByRefCode,
    # InventorySearchAPIView,
    update_inventory_api_view,
    create_inventory_api_view,
    delete_inventory_api_view,
    search_api_view,
)

urlpatterns = [
    path("all/", InventoryListAPIView.as_view()),
    path(
        "user/",
        ListUsersInventoryAPIView.as_view(),
        name="user-inventories",
    ),
    path(
        "details/<str:id>/",
        InventoryDetailView.as_view(),
        name="inventory-details",
    ),
    path(
        "category/<str:query>/",
        InventoryByCategoryAPIView.as_view(),
        name="inventory-by-category",
    ),
    path("product/<str:query>/", InventoryByRefCode.as_view()),
    path("update/<int:sku>/", update_inventory_api_view, name="update-inventory"),
    path("create/", create_inventory_api_view, name="inventory-create"),
    path("delete/<int:sku>/", delete_inventory_api_view, name="delete-inventory"),
    path("search/", search_api_view, name="inventory-search"),
    # path("search/", InventorySearchAPIView.as_view(), name="inventory-search"),
]
