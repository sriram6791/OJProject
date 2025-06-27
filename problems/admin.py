from django.contrib import admin
from .models import Problem, TestCase, Submission

# Register your models here.

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('name','difficulty','created_by','created_at')
    list_filter = ('difficulty','created_at','created_by')
    search_fields = ('name','statement')
    
    def save_model(self,request,obj,form,change):
        if not obj.pk: # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        
@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ('problem','order','is_hidden')
    list_filter = ('problem','is_hidden')
    search_fields = ('problem__name','input_data','expected_output')
    list_editable = ('order','is_hidden')
    
    
@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'problem', 'language', 'status', 'final_verdict', 'submitted_at')
    list_filter = ('status', 'final_verdict', 'language', 'submitted_at')
    search_fields = ('user__username', 'problem__name', 'code')
    readonly_fields = ('user', 'problem', 'code', 'submitted_at', 'execution_time', 'memory_used') # These fields are set by the system