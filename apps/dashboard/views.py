from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q

from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task
from apps.tasks.serializers import TaskSerializer
from apps.projects.serializers import ProjectSerializer


class DashboardView(APIView):
    """
    GET /dashboard/
    Returns a full summary for the authenticated user:
      - task stats (total, by status, overdue)
      - upcoming tasks (due in next 7 days)
      - recent projects
      - overdue tasks list
    """

    def get(self, request):
        user  = request.user
        today = timezone.now().date()
        week  = today + timezone.timedelta(days=7)

        # ── Task counts ────────────────────────────────────────────────────────
        my_tasks = Task.objects.filter(
            assignee=user,
            project__memberships__user=user,
        ).distinct()

        status_counts = {
            item['status']: item['count']
            for item in my_tasks.values('status').annotate(count=Count('id'))
        }

        total_tasks     = my_tasks.count()
        done_tasks      = status_counts.get('done', 0)
        overdue_count   = my_tasks.filter(due_date__lt=today).exclude(status='done').count()
        completion_pct  = round((done_tasks / total_tasks * 100), 1) if total_tasks else 0

        # ── Upcoming tasks (next 7 days, not done) ─────────────────────────────
        upcoming = my_tasks.filter(
            due_date__range=[today, week]
        ).exclude(status='done').select_related('project', 'assignee', 'created_by').order_by('due_date')[:5]

        # ── Overdue tasks ──────────────────────────────────────────────────────
        overdue = my_tasks.filter(
            due_date__lt=today
        ).exclude(status='done').select_related('project', 'assignee', 'created_by').order_by('due_date')[:10]

        # ── My projects summary ─────────────────────────────────────────────────
        my_projects = Project.objects.filter(
            memberships__user=user, status='active'
        ).annotate(
            total_tasks=Count('tasks'),
            done_tasks=Count('tasks', filter=Q(tasks__status='done')),
            overdue_tasks=Count('tasks', filter=Q(tasks__due_date__lt=today) & ~Q(tasks__status='done')),
        ).select_related('created_by').prefetch_related('memberships')[:5]

        # ── Role counts ────────────────────────────────────────────────────────
        admin_count  = ProjectMember.objects.filter(user=user, role='admin').count()
        member_count = ProjectMember.objects.filter(user=user, role='member').count()

        return Response({
            'tasks': {
                'total':          total_tasks,
                'done':           done_tasks,
                'in_progress':    status_counts.get('in_progress', 0),
                'in_review':      status_counts.get('in_review', 0),
                'todo':           status_counts.get('todo', 0),
                'overdue':        overdue_count,
                'completion_pct': completion_pct,
            },
            'projects': {
                'total':          my_projects.count(),
                'as_admin':       admin_count,
                'as_member':      member_count,
            },
            'upcoming_tasks': TaskSerializer(upcoming, many=True, context={'request': request}).data,
            'overdue_tasks':  TaskSerializer(overdue,  many=True, context={'request': request}).data,
            'recent_projects': [
                {
                    'id':           p.id,
                    'name':         p.name,
                    'status':       p.status,
                    'my_role':      p.memberships.filter(user=user).values_list('role', flat=True).first(),
                    'total_tasks':  p.total_tasks,
                    'done_tasks':   p.done_tasks,
                    'overdue_tasks': p.overdue_tasks,
                    'completion_pct': round(p.done_tasks / p.total_tasks * 100, 1) if p.total_tasks else 0,
                }
                for p in my_projects
            ],
        })
