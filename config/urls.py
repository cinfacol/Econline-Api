from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("supersecret/", admin.site.urls),
    path("api/auth/", include("djoser.urls")),
    path("api/auth/", include("djoser.urls.jwt")),
    path("api/profile/", include("profiles.urls")),
    path("api/products/", include("products.urls")),
    path("api/ratings/", include("ratings.urls")),
    path("api/enquiries/", include("enquiries.urls")),
    path("i18n", include("django.conf.urls.i18n")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Ecommerce Online Admin"
admin.site.site_title = "Ecommerce Online Admin Portal"
admin.site.index_title = "Welcome to the Ecommerce Online Portal"
