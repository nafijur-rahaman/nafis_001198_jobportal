from django.urls import path
from . import views

urlpatterns = [
    # Auth & Profiles
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/create/', views.create_profile, name='create-profile'),
    
    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Job crud
    path('', views.JobListView.as_view(), name='job-list'), 
    path('job/<int:pk>/', views.JobDetailView.as_view(), name='job-detail'),
    path('job/new/', views.JobCreateView.as_view(), name='job-create'),
    path('job/<int:pk>/update/', views.JobUpdateView.as_view(), name='job-update'),
    path('job/<int:pk>/delete/', views.JobDeleteView.as_view(), name='job-delete'),
    path('apply/<int:job_id>/', views.apply_for_job, name='apply-job'),
]