from rest_framework import serializers
from . import models
from accounts.models import User
from django.db.models import Avg


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = ["id", "name"]

class CourseAuthorSerialzer(serializers.ModelSerializer):
    total_courses =serializers.SerializerMethodField()
    average_rating =serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["name", "email", "total_courses", "average_rating"]

    def get_average_rating(self, obj: User):
        return round(
            obj.courses.aggregate(average_rating=Avg("average_rating"))["average_rating"] or 0
        )

    def get_total_courses(self, obj: User):
        return obj.courses.count()

class CourseSerializer(serializers.ModelSerializer):
    tag = TagSerializer(many=True, read_only=True)
    author = CourseAuthorSerialzer(read_only=True)
    total_enrollments = serializers.SerializerMethodField()

    class Meta:
        model = models.Course
        fields = "__all__"

    def get_total_enrollments(self, obj: models.Course):
        return (
            obj.enrollments.count()
        )
    
class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="name", read_only=True)

    class Meta:
        model = models.Review
        fields = ["id", "user", "rating", "comment", "created_at"]


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Lesson
        fields = ["id", "title", "description", "video_url", "time_estimate", "created_at"]

class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    class Meta:
        model = models.Module
        fields = ["id", "title", "created_at", "lessons"]
