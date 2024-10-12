from django.urls import path
from .views import (
    GetItemsView,
    AddItemToCartView,
    IncreaseQuantityView,
    DecreaseQuantityView,
    RemoveItemView,
)

urlpatterns = [
    path("cart-items/", GetItemsView.as_view()),
    path("add-item/", AddItemToCartView.as_view()),
    path("increase-quantity/", IncreaseQuantityView.as_view()),
    path("decrease-quantity/", DecreaseQuantityView.as_view()),
    path("remove-item/", RemoveItemView.as_view()),
    path("delivery-cost/", RemoveItemView.as_view()),
]
