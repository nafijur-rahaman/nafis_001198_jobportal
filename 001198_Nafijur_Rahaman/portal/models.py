from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('recruiter', 'Recruiter'),
        ('jobseeker', 'Job Seeker'),
    )
    display_name = models.CharField(max_length=100)
    role = models.CharField(max_length=15, choices=USER_TYPE_CHOICES, blank=True)

class RecruiterProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='recruiter_profile')
    company_information = models.TextField()

class JobSeekerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='jobseeker_profile')
    skills_set = models.CharField(max_length=255)
    resume = models.FileField(upload_to='resumes/',null=True, blank=True)

class JobCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'job categories'

    def __str__(self):
        return self.name

class JobPost(models.Model):
    recruiter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='jobs_posted')
    title = models.CharField(max_length=200)
    number_of_openings = models.PositiveIntegerField()
    category = models.ForeignKey(JobCategory, on_delete=models.PROTECT, related_name='jobs')
    job_description = models.TextField()
    required_skills = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class JobApplication(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
    )

    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='my_applications')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'applicant') 

    def __str__(self):
        return f"{self.applicant.display_name} - {self.job.title}"

    def accept(self):
        if self.status == self.STATUS_ACCEPTED:
            return True
        self.job.refresh_from_db(fields=['number_of_openings'])
        if self.job.number_of_openings < 1:
            return False
        self.status = self.STATUS_ACCEPTED
        self.job.number_of_openings -= 1
        self.job.save(update_fields=['number_of_openings'])
        self.save(update_fields=['status'])
        return True

    def reject(self):
        if self.status == self.STATUS_ACCEPTED:
            self.job.number_of_openings += 1
            self.job.save(update_fields=['number_of_openings'])
        self.status = self.STATUS_REJECTED
        self.save(update_fields=['status'])
        return True
