from .views import CourseViewSet, LessonMarkAsWatchedView, ProcessCheckout
from rest_framework.routers import DefaultRouter
from django.urls import path

router = DefaultRouter()

router.register(r"courses", CourseViewSet, basename="courses")

urlpatterns = router.urls

urlpatterns += [
    path("lessons/<int:pk>/watched/", LessonMarkAsWatchedView.as_view()),
    path("process_checkout", ProcessCheckout.as_view()),
]
