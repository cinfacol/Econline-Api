from django.urls import path

from .views import (
    AttributeValueCreateAPIView,
    AttributeValueListAPIView,
    BrandCreateAPIView,
    BrandListAPIView,
    InventoryByCategoryAPIView,
    InventoryByRefCode,
    InventoryDetailView,
    InventoryImages,
    InventoryListAPIView,
    ListUsersInventoryAPIView,
    TypeCreateAPIView,
    TypeListAPIView,
    create_inventory_api_view,
    delete_inventory_api_view,
    search_api_view,
    update_inventory_api_view,
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
    path("images/", InventoryImages.as_view(), name="inventory-images"),
    path("product/<str:query>/", InventoryByRefCode.as_view()),
    path("update/<int:sku>/", update_inventory_api_view, name="update-inventory"),
    path("create/", create_inventory_api_view, name="inventory-create"),
    path("delete/<int:sku>/", delete_inventory_api_view, name="delete-inventory"),
    path("search/", search_api_view, name="inventory-search"),
    # path("search/", InventorySearchAPIView.as_view(), name="inventory-search"),
    path("brands/create/", BrandCreateAPIView.as_view(), name="brand-create"),
    path("brands/list/", BrandListAPIView.as_view(), name="brand-list"),
    path(
        "attribute-values/list/",
        AttributeValueListAPIView.as_view(),
        name="attribute-value-list",
    ),
    path(
        "attribute-values/create/",
        AttributeValueCreateAPIView.as_view(),
        name="attribute-value-create",
    ),
    path("types/list/", TypeListAPIView.as_view(), name="type-list"),
    path("types/create/", TypeCreateAPIView.as_view(), name="type-create"),
]
