from django.db.models import Sum, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from courses import models
from courses.serializers import CourseSerializer

from rest_framework.request import Request


class DashboardStatsView(APIView):

    def get(self, request: Request):
        user = request.user

        enrollments = (
            models.Enrollment.objects
            .filter(user=user)
            .select_related("course")
        )

        courses = [e.course for e in enrollments]
        courses_data = CourseSerializer(courses, many=True).data

        total_courses = enrollments.count()
        total_reviews = models.Review.objects.filter(user=user).count()

        total_watched_time = (
            models.WatchedLesson.objects
            .filter(user=user)
            .aggregate(total=Sum("lesson__time_estimate"))
            .get("total") or 0
        )

        total_certificates = 0

        for enrollment in enrollments:
            total_lessons = (
                enrollment.course.modules
                .aggregate(total=Count("lessons"))
                .get("total") or 0
            )

            watched_lessons_count = (
                models.WatchedLesson.objects
                .filter(
                    user=user,
                    lesson__module__course=enrollment.course
                )
                .count()
            )

            if total_lessons and watched_lessons_count >= total_lessons:
                total_certificates += 1

        return Response(
            {
                "total_courses": total_courses,
                "total_reviews": total_reviews,
                "total_watched_time": total_watched_time,
                "total_certificates": total_certificates,
                "courses": courses_data,
            },
            status=status.HTTP_200_OK
        )
