from django_filters import rest_framework as filters

from courses.models import Course


"""
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
"""

class CourseFilter(filters.FilterSet):
    title = filters.CharFilter(field_name="title", lookup_expr="icontains")
    tags = filters.BaseInFilter(field_name="tags__name", lookup_expr="in")
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")
    level = filters.CharFilter(field_name="level")
    author = filters.CharFilter(field_name="author__name")
    created_at = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")

    class Meta:
        model = Course