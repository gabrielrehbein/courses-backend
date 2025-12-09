from django.db import models

from accounts.models import User


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)


class Course(models.Model):
    title = models.CharField(max_length=200)
    thumbnail = models.TextField()
    description = models.TextField()
    tags = models.ManyToManyField(Tag, related_name='courses')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_reviews = models.PositiveIntegerField(default=0)
    average_rating = models.PositiveIntegerField(default=0)
    author = models.ForeignKey(
        User,
        related_name='courses',
        on_delete=models.CASCADE
    )
    level = models.TextField(max_length=50, choices=[
        ('beginner', 'Iniciante'),
        ('intermediate', 'Intermediário'),
        ('advanced', 'Avançado')
    ], default='beginner')
    created_at = models.DateTimeField(auto_now_add=True)


class Enrollment(models.Model):
    user = models.ForeignKey(
        User,
        related_name='enrollments',
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course,
        related_name='enrollments',
        on_delete=models.CASCADE
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')


class Module(models.Model):
    course = models.ForeignKey(
        Course,
        related_name='modules',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)


class Lesson(models.Model):
    module = models.ForeignKey(
        Module,
        related_name='lessons',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    time_estimate = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class WatchedLesson(models.Model):
    user = models.ForeignKey(
        User,
        related_name='watched_lessons',
        on_delete=models.CASCADE
    )
    lesson = models.ForeignKey(
        Lesson,
        related_name='watched_by',
        on_delete=models.CASCADE
    )
    watched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'courses_watched_lesson'
        unique_together = ('user', 'lesson')


class Review(models.Model):
    user = models.ForeignKey(
        User,
        related_name='reviews',
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course,
        related_name='reviews',
        on_delete=models.CASCADE
    )
    rating = models.PositiveIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')


class Order(models.Model):
    user = models.ForeignKey(
        User,
        related_name='orders',
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )
    paid = models.BooleanField(default=False)
    external_payment_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
