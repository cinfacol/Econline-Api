from django.urls import path

from .views import *

urlpatterns = [
    path("get-ratings/<productId>", GetProductRatingsView.as_view()),
    path("get-rating/<productId>", GetProductRatingView.as_view()),
    path("create-rating/<productId>", CreateProductRatingView.as_view()),
    path("update-rating/<productId>", UpdateProductRatingView.as_view()),
    path("delete-rating/<productId>", DeleteProductRatingView.as_view()),
    path("filter-ratings/<productId>", FilterProductRatingsView.as_view()),
]
