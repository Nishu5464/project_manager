from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import ProjectMember


def get_membership(user, project):
    """Return the ProjectMember or None."""
    try:
        return ProjectMember.objects.get(project=project, user=user)
    except ProjectMember.DoesNotExist:
        return None


class IsProjectMember(BasePermission):
    """Allow any project member (Admin or Member) to access the project."""
    message = 'You are not a member of this project.'

    def has_object_permission(self, request, view, obj):
        project = obj if hasattr(obj, 'memberships') else obj.project
        return ProjectMember.objects.filter(project=project, user=request.user).exists()


class IsProjectAdmin(BasePermission):
    """Allow only project Admins."""
    message = 'Only project admins can perform this action.'

    def has_object_permission(self, request, view, obj):
        project = obj if hasattr(obj, 'memberships') else obj.project
        return ProjectMember.objects.filter(
            project=project, user=request.user, role=ProjectMember.Role.ADMIN
        ).exists()


class IsProjectAdminOrReadOnly(BasePermission):
    """Admins can write; any member can read."""
    message = 'Only project admins can modify this resource.'

    def has_object_permission(self, request, view, obj):
        project = obj if hasattr(obj, 'memberships') else obj.project
        membership = get_membership(request.user, project)
        if not membership:
            return False
        if request.method in SAFE_METHODS:
            return True
        return membership.role == ProjectMember.Role.ADMIN
