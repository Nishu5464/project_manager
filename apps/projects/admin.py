from django.contrib import admin
from .models import Project, ProjectMember


class ProjectMemberInline(admin.TabularInline):
    model  = ProjectMember
    extra  = 0
    fields = ['user', 'role', 'joined_at']
    readonly_fields = ['joined_at']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display   = ['name', 'status', 'created_by', 'due_date', 'created_at']
    list_filter    = ['status']
    search_fields  = ['name', 'description']
    inlines        = [ProjectMemberInline]


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display  = ['user', 'project', 'role', 'joined_at']
    list_filter   = ['role']
    search_fields = ['user__name', 'user__email', 'project__name']
