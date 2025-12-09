from .views import CourseViewSet
from rest_framework.routers import DefaultRouter


router = DefaultRouter()

router.register(r"courses", CourseViewSet, basename="courses")

urlpatterns = router.urls
