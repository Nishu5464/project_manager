from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from .models import Project, ProjectMember
from .serializers import (
    ProjectSerializer, ProjectDetailSerializer,
    AddMemberSerializer, UpdateMemberRoleSerializer, ProjectMemberSerializer,
)
from .permissions import IsProjectMember, IsProjectAdmin, IsProjectAdminOrReadOnly


class ProjectListCreateView(generics.ListCreateAPIView):
    """
    GET  /projects/      → list projects user belongs to
    POST /projects/      → create project (creator becomes Admin)
    """
    serializer_class = ProjectSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields    = ['name', 'description']
    ordering_fields  = ['created_at', 'name', 'due_date']

    def get_queryset(self):
        return Project.objects.filter(
            memberships__user=self.request.user
        ).distinct().select_related('created_by').prefetch_related('memberships', 'tasks')

    def perform_create(self, serializer):
        project = serializer.save(created_by=self.request.user)
        # Creator automatically becomes Admin
        ProjectMember.objects.create(
            project=project,
            user=self.request.user,
            role=ProjectMember.Role.ADMIN,
        )


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /projects/<id>/  → project detail + members
    PATCH  /projects/<id>/  → update (Admin only)
    DELETE /projects/<id>/  → delete (Admin only)
    """
    def get_queryset(self):
        return Project.objects.filter(
            memberships__user=self.request.user
        ).select_related('created_by').prefetch_related('memberships__user', 'tasks')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProjectDetailSerializer
        return ProjectSerializer

    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT', 'DELETE']:
            return [IsProjectAdmin()]
        return [IsProjectMember()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        instance.delete()
        return Response({'detail': 'Project deleted.'}, status=status.HTTP_204_NO_CONTENT)


class ProjectMemberListView(generics.ListAPIView):
    """GET /projects/<project_pk>/members/"""
    serializer_class = ProjectMemberSerializer

    def get_queryset(self):
        project = get_object_or_404(
            Project,
            pk=self.kwargs['project_pk'],
            memberships__user=self.request.user,
        )
        return project.memberships.select_related('user')


class AddMemberView(APIView):
    """POST /projects/<project_pk>/members/  — Admin only"""

    def post(self, request, project_pk):
        project = get_object_or_404(Project, pk=project_pk, memberships__user=request.user)

        # RBAC check
        membership = project.memberships.filter(user=request.user, role=ProjectMember.Role.ADMIN).first()
        if not membership:
            return Response({'detail': 'Only admins can add members.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = AddMemberSerializer(
            data=request.data,
            context={'project': project, 'request': request},
        )
        serializer.is_valid(raise_exception=True)

        new_member = ProjectMember.objects.create(
            project=project,
            user=serializer.context['member_user'],
            role=serializer.validated_data['role'],
        )
        return Response(ProjectMemberSerializer(new_member).data, status=status.HTTP_201_CREATED)


class MemberDetailView(APIView):
    """
    PATCH  /projects/<project_pk>/members/<user_pk>/  → change role (Admin only)
    DELETE /projects/<project_pk>/members/<user_pk>/  → remove member (Admin only)
    """

    def _get_project_and_check_admin(self, request, project_pk):
        project = get_object_or_404(Project, pk=project_pk, memberships__user=request.user)
        is_admin = project.memberships.filter(user=request.user, role=ProjectMember.Role.ADMIN).exists()
        if not is_admin:
            return project, Response({'detail': 'Only admins can manage members.'}, status=status.HTTP_403_FORBIDDEN)
        return project, None

    def patch(self, request, project_pk, user_pk):
        project, err = self._get_project_and_check_admin(request, project_pk)
        if err:
            return err
        member = get_object_or_404(ProjectMember, project=project, user_id=user_pk)

        serializer = UpdateMemberRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member.role = serializer.validated_data['role']
        member.save()
        return Response(ProjectMemberSerializer(member).data)

    def delete(self, request, project_pk, user_pk):
        project, err = self._get_project_and_check_admin(request, project_pk)
        if err:
            return err
        # Prevent removing the last admin
        if str(request.user.pk) == str(user_pk):
            admin_count = project.memberships.filter(role=ProjectMember.Role.ADMIN).count()
            if admin_count <= 1:
                return Response(
                    {'detail': 'Cannot remove the last admin.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        member = get_object_or_404(ProjectMember, project=project, user_id=user_pk)
        member.delete()
        return Response({'detail': 'Member removed.'}, status=status.HTTP_204_NO_CONTENT)
