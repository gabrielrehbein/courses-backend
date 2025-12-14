from .views import DashboardStatsView
from django.urls import path

urlpatterns = [
    path("dashbord/", DashboardStatsView.as_view()),
]
