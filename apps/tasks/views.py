from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.projects.models import Project, ProjectMember
from .models import Task, Comment
from .serializers import TaskSerializer, TaskDetailSerializer, CommentSerializer
from .filters import TaskFilter


def _get_project_for_user(project_pk, user):
    return get_object_or_404(Project, pk=project_pk, memberships__user=user)


def _is_admin(user, project):
    return ProjectMember.objects.filter(
        user=user, project=project, role=ProjectMember.Role.ADMIN
    ).exists()


class TaskListCreateView(generics.ListCreateAPIView):
    """
    GET  /projects/<project_pk>/tasks/   → list tasks (filterable)
    POST /projects/<project_pk>/tasks/   → create task (any member)
    """
    serializer_class   = TaskSerializer
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class    = TaskFilter
    search_fields      = ['title', 'description']
    ordering_fields    = ['created_at', 'due_date', 'priority', 'status']

    def get_queryset(self):
        project = _get_project_for_user(self.kwargs['project_pk'], self.request.user)
        return project.tasks.select_related('assignee', 'created_by').prefetch_related('comments')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['project'] = _get_project_for_user(self.kwargs['project_pk'], self.request.user)
        return ctx

    def perform_create(self, serializer):
        project = _get_project_for_user(self.kwargs['project_pk'], self.request.user)
        serializer.save(project=project, created_by=self.request.user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /tasks/<pk>/  → task detail + comments
    PATCH  /tasks/<pk>/  → update (Admin OR assignee for status-only)
    DELETE /tasks/<pk>/  → delete (Admin only)
    """
    def get_queryset(self):
        return Task.objects.filter(
            project__memberships__user=self.request.user
        ).select_related('assignee', 'created_by', 'project').prefetch_related('comments__author')

    def get_serializer_class(self):
        return TaskDetailSerializer if self.request.method == 'GET' else TaskSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['project'] = self.get_object().project
        return ctx

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        project = task.project
        admin = _is_admin(request.user, project)

        # Members (non-admin) can only update their own task's status
        if not admin:
            if task.assignee != request.user:
                return Response(
                    {'detail': 'Only the assignee or an admin can update this task.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            allowed = {'status'}
            disallowed = set(request.data.keys()) - allowed
            if disallowed:
                return Response(
                    {'detail': f'Members may only update: {allowed}. Got: {disallowed}'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        task = self.get_object()
        if not _is_admin(request.user, task.project):
            return Response({'detail': 'Only admins can delete tasks.'}, status=status.HTTP_403_FORBIDDEN)
        task.delete()
        return Response({'detail': 'Task deleted.'}, status=status.HTTP_204_NO_CONTENT)


class CommentListCreateView(generics.ListCreateAPIView):
    """
    GET  /tasks/<task_pk>/comments/  → list comments
    POST /tasks/<task_pk>/comments/  → add comment (any member)
    """
    serializer_class = CommentSerializer

    def _get_task(self):
        return get_object_or_404(
            Task,
            pk=self.kwargs['task_pk'],
            project__memberships__user=self.request.user,
        )

    def get_queryset(self):
        return self._get_task().comments.select_related('author')

    def perform_create(self, serializer):
        serializer.save(task=self._get_task(), author=self.request.user)


class CommentDetailView(generics.UpdateAPIView, generics.DestroyAPIView):
    """
    PATCH  /tasks/<task_pk>/comments/<pk>/  → edit own comment
    DELETE /tasks/<task_pk>/comments/<pk>/  → delete own or admin
    """
    serializer_class = CommentSerializer

    def get_queryset(self):
        return Comment.objects.filter(
            task__project__memberships__user=self.request.user
        )

    def update(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return Response({'detail': 'You can only edit your own comments.'}, status=403)
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        is_admin = _is_admin(request.user, comment.task.project)
        if comment.author != request.user and not is_admin:
            return Response({'detail': 'You can only delete your own comments.'}, status=403)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
