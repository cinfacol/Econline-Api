from django.urls import path
from .views import (
    GetItemsView,
    AddItemToCartView,
    # IncreaseQuantityView,
    GetTotalView,
    # GetItemTotalView,
    # UpdateItemView,
    RemoveItemView,
    ClearCartView,
    SynchCartItemsView,
)

urlpatterns = [
    path("cart-items/", GetItemsView.as_view()),
    path("add-item/", AddItemToCartView.as_view()),
    path("get-total/", GetTotalView.as_view()),
    # path("increase-quantity/", IncreaseQuantityView.as_view()),
    # path("get-item-total/", GetItemTotalView.as_view()),
    # path("update-item/", UpdateItemView.as_view()),
    path("remove-item/", RemoveItemView.as_view()),
    path("delivery-cost/", RemoveItemView.as_view()),
    path("clear/", ClearCartView.as_view()),
    path("synch/", SynchCartItemsView.as_view()),
]
