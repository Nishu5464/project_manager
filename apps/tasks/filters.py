import django_filters
from django.utils import timezone
from .models import Task


class TaskFilter(django_filters.FilterSet):
    status   = django_filters.ChoiceFilter(choices=Task.Status.choices)
    priority = django_filters.ChoiceFilter(choices=Task.Priority.choices)
    assignee = django_filters.NumberFilter(field_name='assignee__id')
    overdue  = django_filters.BooleanFilter(method='filter_overdue', label='Overdue')
    due_before = django_filters.DateFilter(field_name='due_date', lookup_expr='lte')
    due_after  = django_filters.DateFilter(field_name='due_date', lookup_expr='gte')

    class Meta:
        model  = Task
        fields = ['status', 'priority', 'assignee', 'overdue', 'due_before', 'due_after']

    def filter_overdue(self, queryset, name, value):
        today = timezone.now().date()
        if value:
            return queryset.filter(due_date__lt=today).exclude(status=Task.Status.DONE)
        return queryset.exclude(due_date__lt=today).filter(status__ne=Task.Status.DONE) \
               if False else queryset
