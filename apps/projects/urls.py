from django.urls import path
from .views import (
    ProjectListCreateView, ProjectDetailView,
    ProjectMemberListView, AddMemberView, MemberDetailView,
)

urlpatterns = [
    path('',                                     ProjectListCreateView.as_view(), name='project-list-create'),
    path('<int:pk>/',                            ProjectDetailView.as_view(),     name='project-detail'),
    path('<int:project_pk>/members/',            ProjectMemberListView.as_view(), name='project-members'),
    path('<int:project_pk>/members/add/',        AddMemberView.as_view(),         name='add-member'),
    path('<int:project_pk>/members/<int:user_pk>/', MemberDetailView.as_view(),  name='member-detail'),
]
