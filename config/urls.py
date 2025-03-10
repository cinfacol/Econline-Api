from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("supersecret/", admin.site.urls),
    path("api/auth/", include("djoser.urls")),
    path("api/auth/", include("users.urls")),
    # path("api/auth/", include("djoser.urls.jwt")),
    path("api/auth/", include("djoser.social.urls")),
    path("api/profile/", include("profiles.urls")),
    path("api/products/", include("products.urls")),
    path("api/categories/", include("categories.urls")),
    path("api/reviews/", include("reviews.urls")),
    path("api/enquiries/", include("enquiries.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/inventory/", include("inventory.urls")),
    path("api/cart/", include("cart.urls")),
    path("api/coupons/", include("coupons.urls")),
    path("api/shipping/", include("shipping.urls")),
    # path("api/payments/", include("payments.urls")),
    path("i18n", include("django.conf.urls.i18n")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Ecommerce Online Admin"
admin.site.site_title = "Ecommerce Online Admin Portal"
admin.site.index_title = "Welcome to the Ecommerce Online Portal"
