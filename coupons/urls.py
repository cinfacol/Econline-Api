from django.urls import path
from .views import *

urlpatterns = [
    path("check/", CheckCouponView.as_view()),
    path("campaign/", CampaignView.as_view()),
]
