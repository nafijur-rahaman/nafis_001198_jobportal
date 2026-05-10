from django.contrib import admin
from .models import CustomUser, RecruiterProfile, JobSeekerProfile, JobCategory, JobPost, JobApplication
from django.contrib.auth.admin import UserAdmin


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'display_name', 'email', 'role', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('display_name', 'email')}),
        ('Permissions', {'fields': ('role', 'is_staff', 'is_active')}),
        ('Groups & Permissions', {'fields': ('groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'display_name', 'email', 'role', 'password1', 'password2'),
        }),
    )

@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'recruiter', 'number_of_openings', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'recruiter__username', 'recruiter__display_name', 'required_skills']




admin.site.register(JobApplication)
admin.site.register(RecruiterProfile)
admin.site.register(JobSeekerProfile)

