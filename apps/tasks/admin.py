from django.contrib import admin
from .models import Task, Comment


class CommentInline(admin.TabularInline):
    model  = Comment
    extra  = 0
    fields = ['author', 'body', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display  = ['title', 'project', 'status', 'priority', 'assignee', 'due_date', 'created_at']
    list_filter   = ['status', 'priority']
    search_fields = ['title', 'description']
    inlines       = [CommentInline]
    raw_id_fields = ['assignee', 'created_by']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display  = ['author', 'task', 'created_at']
    search_fields = ['body', 'author__name']
