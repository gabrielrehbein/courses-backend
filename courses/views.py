from rest_framework.viewsets import ReadOnlyModelViewSet
from .filters import CourseFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Course
from . import serializers
from rest_framework.permissions import AllowAny

class CourseViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.CourseSerializer
    filter_backends = (DjangoFilterBackend,)
    queryset = Course.objects.all().order_by("-created_at")
    permission_classes = [AllowAny]
    filterset_class = CourseFilter 
    ordering_fields = ["price", "created_at"]
