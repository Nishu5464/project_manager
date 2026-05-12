from django.urls import path
from .views import (
    TaskListCreateView, TaskDetailView,
    CommentListCreateView, CommentDetailView,
)

urlpatterns = [
    # Tasks nested under projects
    path('project/<int:project_pk>/',         TaskListCreateView.as_view(),  name='task-list-create'),

    # Task detail (no project_pk needed — task pk is globally unique)
    path('<int:pk>/',                          TaskDetailView.as_view(),      name='task-detail'),

    # Comments
    path('<int:task_pk>/comments/',            CommentListCreateView.as_view(), name='comment-list-create'),
    path('<int:task_pk>/comments/<int:pk>/',   CommentDetailView.as_view(),     name='comment-detail'),
]
