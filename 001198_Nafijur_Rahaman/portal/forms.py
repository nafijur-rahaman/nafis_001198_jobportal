from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, RecruiterProfile, JobSeekerProfile, JobPost


class CustomUserRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'display_name', 'email', 'role']

    role = forms.ChoiceField(choices=CustomUser.USER_TYPE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
            
class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['display_name', 'email']
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class RecruiterProfileForm(forms.ModelForm):
    class Meta:
        model = RecruiterProfile
        fields = ['company_information']
        labels = {
            'company_information': 'Company Information',
        }
        help_texts = {
            'company_information': 'Write your company name, address, industry, and short description.',
        }
        widgets = {
            'company_information': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = ['skills_set', 'resume']
        labels = {
            'skills_set': 'Skills',
            'resume': 'Resume',
        }
        help_texts = {
            'skills_set': 'Enter skills separated by commas, for example: Python, Django, HTML.',
            'resume': 'Upload your latest resume file.',
        }
        widgets = {
            'skills_set': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Python, Django, HTML'}),
            'resume': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class JobPostForm(forms.ModelForm):
    class Meta:
        model = JobPost
        fields = ['title', 'number_of_openings', 'category', 'job_description', 'required_skills']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'number_of_openings': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'job_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'required_skills': forms.TextInput(attrs={'class': 'form-control'}),
        }
