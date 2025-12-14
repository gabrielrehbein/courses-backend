from datetime import datetime
from django.db.models import Avg, Count, Sum
from core.utils.exceptions import ValidationError
from rest_framework.exceptions import NotFound
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import decorators
from .filters import CourseFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Course, Enrollment, Lesson, Module, Order, WatchedLesson
from . import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status, views
from django.shortcuts import get_object_or_404, redirect
from django.conf import settings
import stripe


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
        MESSAGE_ERROR = "Você precisa ter o curso para avaliá-lo."
        user, course = self.__get_course_and_user_validate_enrolment(
            request,
            pk,
            MESSAGE_ERROR
        )

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

    def __get_course_and_user_validate_enrolment(self, request, course_pk, required_enrollment):
        user = request.user

        course = get_object_or_404(Course, pk=course_pk)

        is_enrolled = Enrollment.objects.filter(
            course=course, user=user).exists()
        if required_enrollment and not is_enrolled:
            raise ValidationError(
                "Você pricesa estar matriculado neste curso.")
        if not required_enrollment and is_enrolled:
            raise ValidationError("Você já está matriculado neste curso.")

        return user, course

    def __get_course_progress(self, course_pk, user_pk):
        total_lessons = Lesson.objects.filter(
            module__course=course_pk
        ).count()

        total_watched_lessons = WatchedLesson.objects.filter(
            lesson__module__course=course_pk,
            user=user_pk
        ).count()

        if total_lessons <= 0:
            return 100
        if total_watched_lessons <= 0:
            return 0
        return round((total_watched_lessons / total_lessons) * 100, 2)

    @decorators.action(methods=["post"], detail=True, permission_classes=[IsAuthenticated])
    def generate_certificate(self, request, pk):

        MAX_PROGRESS = 100

        MESSAGE_ERROR = "Você deve ter o curso e/ou completa-lo para obter o certificado"
        user, course = self.__get_course_and_user_validate_enrolment(
            request,
            pk,
        )

        progress = self.__get_course_progress(
            course_pk=course.id, user_pk=user.id)

        if (progress < MAX_PROGRESS):
            raise ValidationError(MESSAGE_ERROR)

        course_data = serializers.CourseSerializer(course).data

        certificate_data = {
            "progress": progress,
            "issued_at": datetime.now()
        }

        return Response(
            {
                "course": course_data,
                "certificate": certificate_data
            }, status=status.HTTP_201_CREATED)

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

    @decorators.action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def enroll(self, request: Request, pk=None):
        user, course = self.__get_course_and_user_validate_enrolment(
            request,
            course_pk=pk,
            required_enrollment=False
        )

        if Order.objects.filter(user=user, course=course, paid=True).exists():
            raise ValidationError(
                "Você já tem um pedido para este curso pago.")

        user.orders.filter(course=course, paid=False).delete()

        order = Order.objects.create(
            user=user,
            course=course
        )

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                mode="payment",
                line_items=[
                    {
                        "price_data": {
                            "currency": "brl",
                            "product_data": {
                                "name": course.title,
                                "description": course.description,
                            },
                            "unit_amount": int(course.price * 100),
                        },
                        "quantity": 1,

                    },
                ],
                customer_email=user.email,
                metadata={
                    "user_id": user.id,
                    "order_id": order.id,
                    "course_id": course.id
                },
                success_url=f"{settings.BASE_URL}/api/v1/courses/process_checkout?order_id={order.id}",
                cancel_url=f"{settings.FRONTEND_BASE_URL}/courses/{course.id}?message=cancel_order",
            )

            order.external_payment_id = checkout_session.id
            order.save()

            return Response({"checkout_url": checkout_session.url}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "detail": "Erro ao tentar se inscrever no curso"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LessonMarkAsWatchedView(views.APIView):

    def post(self, request, pk=None):
        lesson = Lesson.objects.filter(id=pk).first()

        if not lesson:
            return Response(
                {"detail": "Aula não encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )

        is_enrolled = Enrollment.objects.filter(
            user=request.user,
            course=lesson.module.course
        ).exists()

        if not is_enrolled:
            return Response(
                {"detail": "Você não está matriculado neste curso"},
                status=status.HTTP_403_FORBIDDEN
            )

        watched, created = WatchedLesson.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )

        if created:
            return Response(
                {"detail": "Aula marcada como assistida"},
                status=status.HTTP_201_CREATED
            )

        return Response(
            {"detail": "Aula já estava marcada como assistida"},
            status=status.HTTP_200_OK
        )


class ProcessCheckout(views.APIView):
    def get(self, request: Request):
        order_id = request.data.get("order_id")

        if not order_id:
            return redirect(settings.FRONTEND_BASE_URL)

        order = get_object_or_404(Order, pk=order_id)

        error_url = f"{settings.FRONTEND_BASE_URL}/courses/{order.course.id}/?message=payment_failed"
        success_url = f"{settings.FRONTEND_BASE_URL}/courses/{order.course.id}/learn/"

        try:
            session = stripe.checkout.Session.retrieve(
                order.external_payment_id)

            if session.payment_status != "paid":
                return redirect(error_url)

            order.paid = True
            order.save()

            Enrollment.objects.get_or_create(
                user=order.user,
                course=order.course
            )

            return redirect(success_url)
        except Exception as e:
            return redirect(error_url)
