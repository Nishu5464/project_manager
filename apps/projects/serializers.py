from rest_framework import serializers
from .models import Project, ProjectMember
from apps.accounts.serializers import UserSerializer


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model  = ProjectMember
        fields = ['id', 'user', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class AddMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role  = serializers.ChoiceField(choices=ProjectMember.Role.choices, default=ProjectMember.Role.MEMBER)

    def validate_email(self, value):
        from apps.accounts.models import User
        try:
            self.context['member_user'] = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('No user found with this email.')
        return value

    def validate(self, attrs):
        project = self.context['project']
        user    = self.context['member_user']
        if ProjectMember.objects.filter(project=project, user=user).exists():
            raise serializers.ValidationError('This user is already a project member.')
        return attrs


class UpdateMemberRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=ProjectMember.Role.choices)


class ProjectSerializer(serializers.ModelSerializer):
    created_by  = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    task_count   = serializers.SerializerMethodField()
    my_role      = serializers.SerializerMethodField()

    class Meta:
        model  = Project
        fields = [
            'id', 'name', 'description', 'status',
            'due_date', 'created_by', 'member_count',
            'task_count', 'my_role', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_member_count(self, obj):
        return obj.memberships.count()

    def get_task_count(self, obj):
        return obj.tasks.count()

    def get_my_role(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        membership = obj.memberships.filter(user=request.user).first()
        return membership.role if membership else None


class ProjectDetailSerializer(ProjectSerializer):
    members = ProjectMemberSerializer(source='memberships', many=True, read_only=True)

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ['members']
