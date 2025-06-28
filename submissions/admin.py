# submissions/admin.py

from django.contrib import admin
from .models import Submission

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'problem', 'language', 'status', 'final_verdict', 'submitted_at', 'execution_time', 'memory_used')
    list_filter = ('status', 'final_verdict', 'language', 'submitted_at')
    search_fields = ('user__username', 'problem__name', 'code', 'error_message')
    readonly_fields = ('user', 'problem', 'code', 'submitted_at', 'execution_time', 'memory_used', 'passed_test_cases', 'total_test_cases', 'error_message')
    fieldsets = (
        (None, {
            'fields': ('user', 'problem', 'code', 'language', 'submitted_at')
        }),
        ('Evaluation Results', {
            'fields': ('status', 'final_verdict', 'passed_test_cases', 'total_test_cases', 'execution_time', 'memory_used', 'error_message')
        }),
    )