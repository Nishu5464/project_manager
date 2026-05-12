from rest_framework import serializers
from django.utils import timezone
from .models import Task, Comment
from apps.accounts.serializers import UserSerializer


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model  = Comment
        fields = ['id', 'author', 'body', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']


class TaskSerializer(serializers.ModelSerializer):
    assignee    = UserSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.accounts.models', fromlist=['User']).User.objects.all(),
        source='assignee', allow_null=True, required=False, write_only=True,
    )
    created_by  = UserSerializer(read_only=True)
    is_overdue  = serializers.BooleanField(read_only=True)
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model  = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'due_date', 'project', 'assignee', 'assignee_id',
            'created_by', 'is_overdue', 'comment_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'project', 'created_by', 'created_at', 'updated_at']

    def get_comment_count(self, obj):
        return obj.comments.count()

    def validate_due_date(self, value):
        if value and value < timezone.now().date():
            raise serializers.ValidationError('Due date cannot be in the past.')
        return value

    def validate_assignee(self, user):
        """Ensure assignee is a member of the project."""
        project = self.context.get('project')
        if user and project:
            from apps.projects.models import ProjectMember
            if not ProjectMember.objects.filter(project=project, user=user).exists():
                raise serializers.ValidationError('Assignee must be a project member.')
        return user


class TaskDetailSerializer(TaskSerializer):
    comments = CommentSerializer(many=True, read_only=True)

    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ['comments']
