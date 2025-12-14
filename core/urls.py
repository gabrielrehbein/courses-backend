from django.contrib import admin
from django.urls import path, include

PREFIX_API_URL = "api/v1/"

urlpatterns = [
    path('admin/', admin.site.urls),

    path(f"{PREFIX_API_URL}", include("accounts.urls")),
    path(f"{PREFIX_API_URL}", include("courses.urls")),
    path(f"{PREFIX_API_URL}", include("courses.urls")),
    path(f"{PREFIX_API_URL}", include("dashboard.urls")),
]
