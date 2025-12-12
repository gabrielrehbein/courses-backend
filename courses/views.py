from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import decorators
from .filters import CourseFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Course, Enrollment, Lesson, Module, WatchedLesson
from . import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from accounts.models import User
from rest_framework import status, views
from rest_framework.exceptions import APIException, NotFound
from core.utils.exceptions import ValidationError
from django.db.models import Avg, Count, Sum


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

    @decorators.action(methods=["get"], detail=True, permission_classes=[IsAuthenticated])
    def content(self, request, pk):
        modules_by_course_detail = Module.objects.filter(
            course=pk
        )

        total_modules = 0
        total_time = 0
        total_lessons = 0
        progress = 0

        modules_serializer = serializers.ModuleSerializer([], many=True)

        if modules_by_course_detail:
            total_modules = modules_by_course_detail.count()

            lesson_aggregate = Lesson.objects.filter(
                module__course=pk
            ).aggregate(
                total_time=Sum("time_estimate"),
                total_lessons=Count("id")
            )

            total_time = lesson_aggregate["total_time"] or 0
            total_lessons = lesson_aggregate["total_lessons"] or 0

            if request.user.is_authenticated:
                total_watched = WatchedLesson.objects.filter(
                    user=request.user,
                    lesson__module__course=pk
                ).aggregate(
                    total_watched=Count("id")
                )["total_watched"] or 0

                if total_lessons > 0:
                    progress = round((total_watched / total_lessons) * 100, 2)

            modules = Module.objects.filter(
                course=pk
            )
            modules_serializer = serializers.ModuleSerializer(
                modules, many=True
            )

        data = {
            "total_modules": total_modules,
            "total_time": total_time,
            "total_lessons": total_lessons,
            "progress": progress,
            "modules": modules_serializer.data
        }

        return Response(data, status=status.HTTP_200_OK)


class LessonMarkAsWatchedView(views.APIView):
    def post(self, request, pk=None):
        lesson = Lesson.objects.filter(
            id=pk
        ).first()

        if (not lesson):
            return NotFound("Aula não encontrada.")

        watched, created = WatchedLesson.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )

        if (created):
            return Response({"detail": "Tarefa marcada como assistida"}, status=status.HTTP_201_CREATED)
        return Response({"detail": "Tarefa já está marcada como assistida"}, status=status.HTTP_201_CREATED)
