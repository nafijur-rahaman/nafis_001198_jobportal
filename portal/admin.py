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


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['job', 'applicant', 'status', 'applied_at']
    list_filter = ['status', 'job__category', 'applied_at']
    search_fields = ['job__title', 'applicant__username', 'applicant__display_name']
    actions = ['accept_applications', 'reject_applications']

    @admin.action(description='Accept selected applications')
    def accept_applications(self, request, queryset):
        accepted = 0
        skipped = 0
        for application in queryset.select_related('job'):
            if application.accept():
                accepted += 1
            else:
                skipped += 1
        if accepted:
            self.message_user(request, f"{accepted} application(s) accepted.")
        if skipped:
            self.message_user(request, f"{skipped} application(s) skipped because no positions were available.", level='warning')

    @admin.action(description='Reject selected applications')
    def reject_applications(self, request, queryset):
        rejected = 0
        for application in queryset.select_related('job'):
            application.reject()
            rejected += 1
        self.message_user(request, f"{rejected} application(s) rejected.")


admin.site.register(RecruiterProfile)
admin.site.register(JobSeekerProfile)

