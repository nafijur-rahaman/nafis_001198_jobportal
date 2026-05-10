from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('recruiter', 'Recruiter'),
        ('jobseeker', 'Job Seeker'),
    )
    display_name = models.CharField(max_length=100)
    role = models.CharField(max_length=15, choices=USER_TYPE_CHOICES)

class RecruiterProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='recruiter_profile')
    company_information = models.TextField()

class JobSeekerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='jobseeker_profile')
    skills_set = models.CharField(max_length=255)
    resume = models.FileField(upload_to='resumes/',null=True, blank=True)

class JobPost(models.Model):
    recruiter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='jobs_posted')
    title = models.CharField(max_length=200)
    number_of_openings = models.PositiveIntegerField()
    category = models.CharField(max_length=100)
    job_description = models.TextField()
    required_skills = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

class JobApplication(models.Model):
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='my_applications')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'applicant') 
