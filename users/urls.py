from django.urls import path, re_path
from .views import (
    CustomProviderAuthView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    LogoutView,
    HealthView,
    AddressListView,
    AddressCreateView,
    AddressUpdateView,
    AddressDeleteView,
    SetDefaultAddressView,
)

urlpatterns = [
    re_path(
        r"^o/(?P<provider>\S+)/$",
        CustomProviderAuthView.as_view(),
        name="provider-auth",
    ),
    path("jwt/create/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("jwt/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("jwt/verify/", CustomTokenVerifyView.as_view(), name="token_verify"),
    path("logout/", LogoutView.as_view(), name="auth_logout"),
    path("health/", HealthView.as_view(), name="docker_health"),
    path("address/", AddressListView.as_view(), name="Address"),
    path("address/create/", AddressCreateView.as_view(), name="new_address"),
    path("address/edit/<uuid:id>", AddressUpdateView.as_view(), name="edit_address"),
    path(
        "address/delete/<uuid:id>",
        AddressDeleteView.as_view(),
        name="delete_address",
    ),
    path(
        "address/default/<uuid:id>",
        SetDefaultAddressView.as_view(),
        name="default_address",
    ),
]
