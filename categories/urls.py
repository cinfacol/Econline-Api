from django.urls import path

from .views import ListCategoriesView

urlpatterns = [
    path("all/", ListCategoriesView.as_view()),
]
