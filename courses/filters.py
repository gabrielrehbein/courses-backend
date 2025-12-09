from django_filters import rest_framework as filters

from courses.models import Course


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
        fields = "__all__"