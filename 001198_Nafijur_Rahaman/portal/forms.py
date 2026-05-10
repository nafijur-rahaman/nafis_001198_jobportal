from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, RecruiterProfile, JobSeekerProfile, JobPost


class CustomUserRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'display_name', 'email', 'role']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            
class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class RecruiterProfileForm(forms.ModelForm):
    class Meta:
        model = RecruiterProfile
        fields = ['company_information']
        widgets = {
            'company_information': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = ['skills_set', 'resume']
        widgets = {
            'skills_set': forms.TextInput(attrs={'class': 'form-control'}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
        }


class JobPostForm(forms.ModelForm):
    class Meta:
        model = JobPost
        fields = ['title', 'number_of_openings', 'category', 'job_description', 'required_skills']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'number_of_openings': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'job_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'required_skills': forms.TextInput(attrs={'class': 'form-control'}),
        }