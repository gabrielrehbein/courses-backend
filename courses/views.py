from rest_framework.viewsets import ReadOnlyModelViewSet
from .filters import CourseFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Course, Enrollment
from . import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.request import Request


class CourseViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.CourseSerializer
    filter_backends = (DjangoFilterBackend,)
    queryset = Course.objects.all().order_by("-created_at")
    permission_classes = [AllowAny]
    filterset_class = CourseFilter
    ordering_fields = ["price", "created_at"]

    def retrieve(self, request: Request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        enrolled_at = None

        if request.user.is_authenticated:
            enrolled = Enrollment.objects.filter(
                user=request.user,
                course=instance
            ).first()

            if enrolled:
                enrolled_at = enrolled.enrolled_at

        return Response(
            {
                **serializer.data,
                "enrolled_at": enrolled_at
            }
        )
