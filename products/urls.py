from django.urls import path

from . import views

urlpatterns = [
    path("list/", views.ProductListView.as_view(), name="product-list"),
    path("create/", views.ProductCreateView.as_view(), name="product-create"),
    path("update/<int:pk>/", views.ProductUpdateView.as_view(), name="product-update"),
    path("delete/<int:pk>/", views.ProductDeleteView.as_view(), name="product-delete"),
]
