from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import decorators
from .filters import CourseFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Course, Enrollment
from . import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from accounts.models import User
from rest_framework import status
from rest_framework.exceptions import APIException
from core.utils.exceptions import ValidationError
from django.db.models import Avg, Count


class CourseViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.CourseSerializer
    filter_backends = (DjangoFilterBackend,)
    queryset = Course.objects.all().order_by("-created_at")
    permission_classes = [AllowAny]
    filterset_class = CourseFilter
    ordering_fields = ["price", "created_at"]

    @decorators.action(methods=["get"], detail=True)
    def reviews(self, request: Request, pk=None):
        course = self.get_object()
        reviews = course.reviews.all()
        serializer = serializers.ReviewSerializer(reviews, many=True)

        return Response(serializer.data)

    @decorators.action(methods=["post"], detail=True, permission_classes=[IsAuthenticated])
    def create_reviews(self, request: Request, pk=None):
        user = request.user
        course = self.get_object()

        if (not Enrollment.objects.filter(user=user, course=course).exists()):
            raise ValidationError("Você precisa ter o curso para avaliá-lo.")

        exists = user.reviews.filter(
            course=course
        ).exists()

        if (exists):
            raise ValidationError("Você já avaliou este curso.")

        data = {
            "rating": request.data.get("rating"),
            "comment": request.data.get("comment"),
        }

        serializer = serializers.ReviewSerializer(data=data)

        if (not serializer.is_valid()):
            raise ValidationError(serializer.errors)

        serializer.save(user=user, course=course)

        aggregate = course.reviews.aggregate(
            average_rating=Avg("rating"),
            total_reviews=Count("id"),
        )

        course.average_rating = aggregate["average_rating"] or 0
        course.total_reviews = aggregate["total_reviews"] or 0

        course.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
