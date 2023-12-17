from django.urls import path

from . import views

urlpatterns = [
    path("all/", views.ListAllProductsAPIView.as_view(), name="all-products"),
    path(
        "agents/", views.ListAgentsProductsAPIView.as_view(), name="agent-products"
    ),
    path("create/", views.create_product_api_view, name="product-create"),
    path(
        "details/<slug:slug>/",
        views.ProductDetailView.as_view(),
        name="product-details",
    ),
    path("update/<slug:slug>/", views.update_product_api_view, name="update-product"),
    path("delete/<slug:slug>/", views.delete_product_api_view, name="delete-product"),
    path("search/", views.ProductSearchAPIView.as_view(), name="product-search"),
]