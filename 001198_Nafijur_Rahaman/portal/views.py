from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q

from .models import JobPost, JobApplication, JobSeekerProfile
from .forms import (
    CustomUserRegistrationForm, UserLoginForm, 
    RecruiterProfileForm, JobSeekerProfileForm, JobPostForm
)


def register_user(request):
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome {user.display_name}! Please complete your profile.")
            return redirect('create-profile')
    else:
        form = CustomUserRegistrationForm()
    return render(request, 'portal/register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('job-list')
    else:
        form = UserLoginForm()
    return render(request, 'portal/login.html', {'form': form})

def logout_user(request):
    logout(request)
    return redirect('login')

@login_required
def create_profile(request):
    user = request.user
    FormClass = RecruiterProfileForm if user.role == 'recruiter' else JobSeekerProfileForm

    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = user
            profile.save()
            return redirect('job-list')
    else:
        form = FormClass()
    return render(request, 'portal/create_profile.html', {'form': form, 'role': user.role})


@login_required
def dashboard(request):
    user = request.user
    if user.role == 'recruiter':
        my_jobs = JobPost.objects.filter(recruiter=user).order_by('-created_at')
        return render(request, 'portal/recruiter_dashboard.html', {'jobs': my_jobs})
        
    elif user.role == 'jobseeker':
        try:
            user_skills = set(x.strip().lower() for x in user.jobseeker_profile.skills_set.split(','))
        except JobSeekerProfile.DoesNotExist:
            user_skills = set()

        matched_jobs = [job for job in JobPost.objects.all() if user_skills.intersection(set(x.strip().lower() for x in job.required_skills.split(',')))]
        my_applications = JobApplication.objects.filter(applicant=user)
        
        return render(request, 'portal/jobseeker_dashboard.html', {
            'matched_jobs': matched_jobs, 'my_applications': my_applications
        })

# --- JOB ACTIONS ---
@login_required
def apply_for_job(request, job_id):
    if request.user.role != 'jobseeker':
        messages.error(request, "Only job seekers can apply.")
        return redirect('job-list')

    job = get_object_or_404(JobPost, id=job_id)
    if not JobApplication.objects.filter(job=job, applicant=request.user).exists():
        JobApplication.objects.create(job=job, applicant=request.user)
        messages.success(request, f"Applied for {job.title}!")
    return redirect('job-detail', pk=job.id)

# --- CRUD CLASS BASED VIEWS ---
class JobListView(ListView):
    model = JobPost
    template_name = 'portal/job_list.html'
    context_object_name = 'jobs'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return JobPost.objects.filter(
                Q(title__icontains=query) | Q(category__icontains=query) | Q(required_skills__icontains=query)
            ).order_by('-created_at')
        return JobPost.objects.all().order_by('-created_at')

class JobDetailView(DetailView):
    model = JobPost
    template_name = 'portal/job_detail.html'
    context_object_name = 'job'

class JobCreateView(LoginRequiredMixin, CreateView):
    model = JobPost
    form_class = JobPostForm
    template_name = 'portal/job_form.html'
    success_url = reverse_lazy('job-list')

    def form_valid(self, form):
        form.instance.recruiter = self.request.user
        return super().form_valid(form)

class JobUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = JobPost
    form_class = JobPostForm
    template_name = 'portal/job_form.html'
    
    def get_success_url(self): return reverse_lazy('job-detail', kwargs={'pk': self.object.pk})
    def test_func(self): return self.request.user == self.get_object().recruiter

class JobDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = JobPost
    template_name = 'portal/job_confirm_delete.html'
    success_url = reverse_lazy('job-list')
    def test_func(self): return self.request.user == self.get_object().recruiter