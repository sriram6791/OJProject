from django.contrib import admin
from .models import Problem, TestCase
from submissions.models import Submission

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
    
