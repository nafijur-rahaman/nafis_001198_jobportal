from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.views.decorators.http import require_POST

from .models import JobPost, JobApplication, JobCategory, JobSeekerProfile
from .forms import (
    CustomUserRegistrationForm, UserLoginForm, 
    RecruiterProfileForm, JobSeekerProfileForm, JobCategoryForm, JobPostForm, UserProfileForm
)


def split_skills(skill_text):
    return {skill.strip().lower() for skill in skill_text.split(',') if skill.strip()}


def register_user(request):
    if request.user.is_authenticated:
        return redirect('job-list')

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
    if request.user.is_authenticated:
        return redirect('job-list')

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
    profile_attr = 'recruiter_profile' if user.role == 'recruiter' else 'jobseeker_profile'

    if hasattr(user, profile_attr):
        messages.info(request, "Your profile is already complete.")
        return redirect('dashboard')

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
def profile(request):
    user = request.user
    profile_obj = None
    profile_skills = []

    if user.role == 'recruiter':
        profile_obj = getattr(user, 'recruiter_profile', None)
    elif user.role == 'jobseeker':
        profile_obj = getattr(user, 'jobseeker_profile', None)
        if profile_obj:
            profile_skills = [skill.strip() for skill in profile_obj.skills_set.split(',') if skill.strip()]

    return render(request, 'portal/profile.html', {'profile_obj': profile_obj, 'profile_skills': profile_skills})


@login_required
def update_profile(request):
    user = request.user

    if user.role == 'recruiter':
        profile_obj = getattr(user, 'recruiter_profile', None)
        FormClass = RecruiterProfileForm
    elif user.role == 'jobseeker':
        profile_obj = getattr(user, 'jobseeker_profile', None)
        FormClass = JobSeekerProfileForm
    else:
        messages.error(request, "Please choose a valid account role before updating your profile.")
        return redirect('job-list')

    if profile_obj is None:
        messages.info(request, "Please complete your profile first.")
        return redirect('create-profile')

    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=user)
        profile_form = FormClass(request.POST, request.FILES, instance=profile_obj)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        user_form = UserProfileForm(instance=user)
        profile_form = FormClass(instance=profile_obj)

    return render(request, 'portal/update_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'role': user.role,
    })


@login_required
def dashboard(request):
    user = request.user
    if user.role == 'recruiter':
        my_jobs = JobPost.objects.filter(recruiter=user).prefetch_related('applications__applicant').order_by('-created_at')
        applications = JobApplication.objects.filter(job__recruiter=user).select_related('job', 'applicant').order_by('-applied_at')
        return render(request, 'portal/recruiter_dashboard.html', {'jobs': my_jobs, 'applications': applications})
        
    elif user.role == 'jobseeker':
        try:
            user_skills = split_skills(user.jobseeker_profile.skills_set)
        except JobSeekerProfile.DoesNotExist:
            user_skills = set()

        matched_jobs = []
        for job in JobPost.objects.select_related('recruiter', 'category').all():
            matched_skills = sorted(user_skills.intersection(split_skills(job.required_skills)))
            if matched_skills:
                matched_jobs.append({
                    'job': job,
                    'matched_skills': matched_skills,
                    'match_count': len(matched_skills),
                })

        matched_jobs.sort(key=lambda item: item['match_count'], reverse=True)
        my_applications = JobApplication.objects.filter(applicant=user)
        
        return render(request, 'portal/jobseeker_dashboard.html', {
            'matched_jobs': matched_jobs, 'my_applications': my_applications
        })

    messages.error(request, "Please choose a valid account role before using the dashboard.")
    return redirect('job-list')

# --- JOB ACTIONS ---
@login_required
@require_POST
def apply_for_job(request, job_id):
    if request.user.role != 'jobseeker':
        messages.error(request, "Only job seekers can apply.")
        return redirect('job-list')

    with transaction.atomic():
        job = get_object_or_404(JobPost.objects.select_for_update(), id=job_id)
        if JobApplication.objects.filter(job=job, applicant=request.user).exists():
            messages.info(request, "You already applied for this job.")
            return redirect('job-detail', pk=job.id)

        if job.number_of_openings < 1:
            messages.error(request, "This job has no open positions left.")
            return redirect('job-detail', pk=job.id)

        JobApplication.objects.create(job=job, applicant=request.user)
        job.number_of_openings -= 1
        job.save(update_fields=['number_of_openings'])
        messages.success(request, f"Applied for {job.title}!")
    return redirect('job-detail', pk=job.id)


@login_required
def application_detail(request, application_id):
    application = get_object_or_404(
        JobApplication.objects.select_related('job', 'applicant', 'applicant__jobseeker_profile'),
        id=application_id,
        job__recruiter=request.user,
    )
    profile_obj = getattr(application.applicant, 'jobseeker_profile', None)
    profile_skills = []
    if profile_obj:
        profile_skills = [skill.strip() for skill in profile_obj.skills_set.split(',') if skill.strip()]

    return render(request, 'portal/application_detail.html', {
        'application': application,
        'profile_obj': profile_obj,
        'profile_skills': profile_skills,
    })


@login_required
@require_POST
def accept_application(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id, job__recruiter=request.user)
    if application.accept():
        messages.success(request, "Application accepted.")
    else:
        messages.error(request, "No open positions are available for this job.")
    return redirect('application-detail', application_id=application.id)


@login_required
@require_POST
def reject_application(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id, job__recruiter=request.user)
    application.reject()
    messages.success(request, "Application rejected.")
    return redirect('application-detail', application_id=application.id)

# --- CRUD CLASS BASED VIEWS ---
class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "Only staff users can manage categories.")
        return redirect('job-list')


class JobCategoryListView(StaffRequiredMixin, ListView):
    model = JobCategory
    template_name = 'portal/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return JobCategory.objects.prefetch_related('jobs').order_by('name')


class JobCategoryCreateView(StaffRequiredMixin, CreateView):
    model = JobCategory
    form_class = JobCategoryForm
    template_name = 'portal/category_form.html'
    success_url = reverse_lazy('category-list')

    def form_valid(self, form):
        messages.success(self.request, "Category added successfully.")
        return super().form_valid(form)


class JobCategoryUpdateView(StaffRequiredMixin, UpdateView):
    model = JobCategory
    form_class = JobCategoryForm
    template_name = 'portal/category_form.html'
    success_url = reverse_lazy('category-list')

    def form_valid(self, form):
        messages.success(self.request, "Category updated successfully.")
        return super().form_valid(form)


class JobCategoryDeleteView(StaffRequiredMixin, DeleteView):
    model = JobCategory
    template_name = 'portal/category_confirm_delete.html'
    success_url = reverse_lazy('category-list')

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "This category cannot be deleted because it has job posts.")
            return redirect('category-list')
        messages.success(self.request, "Category deleted successfully.")
        return response


class JobListView(ListView):
    model = JobPost
    template_name = 'portal/job_list.html'
    context_object_name = 'jobs'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return JobPost.objects.filter(
                Q(title__icontains=query) | Q(category__name__icontains=query) | Q(required_skills__icontains=query)
            ).order_by('-created_at')
        return JobPost.objects.all().order_by('-created_at')

class JobDetailView(DetailView):
    model = JobPost
    template_name = 'portal/job_detail.html'
    context_object_name = 'job'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated and user.role == 'jobseeker':
            context['application'] = JobApplication.objects.filter(job=self.object, applicant=user).first()
        return context

class JobCreateView(LoginRequiredMixin, CreateView):
    model = JobPost
    form_class = JobPostForm
    template_name = 'portal/job_form.html'
    success_url = reverse_lazy('job-list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.role != 'recruiter':
            messages.error(request, "Only recruiters can post jobs.")
            return redirect('job-list')
        return super().dispatch(request, *args, **kwargs)

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
