from django.urls import path

from .views import (
    ListCategoriesView,
    CreateCategoryView,
    ListMeasureUnitsView,
    CreateMeasureUnitView,
)

urlpatterns = [
    path("all/", ListCategoriesView.as_view()),
    path("create/", CreateCategoryView.as_view()),
    path("measure-units/", ListMeasureUnitsView.as_view()),
    path("measure-units/create/", CreateMeasureUnitView.as_view()),
]
