from django import forms
from .models import Contest, ContestProblem
from problems.models import Problem
from django.forms import inlineformset_factory
from django.utils import timezone

class ContestForm(forms.ModelForm):
    """Form for creating and editing contests"""
    
    class Meta:
        model = Contest
        fields = ['name', 'description', 'start_time', 'end_time']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter contest name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Enter contest description'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            # Validate that end_time is after start_time
            if end_time <= start_time:
                raise forms.ValidationError("End time must be after start time.")
                
            # Validate that start_time is not in the past
            # Use date comparison instead of exact datetime to allow for same-day contests
            now = timezone.now()
            if start_time.date() < now.date():
                raise forms.ValidationError("Start time cannot be in the past (before today).")
        
        return cleaned_data

class ContestProblemForm(forms.ModelForm):
    """Form for adding problems to a contest"""
    
    class Meta:
        model = ContestProblem
        fields = ['problem', 'points', 'order_in_contest']
        widgets = {
            'problem': forms.Select(attrs={'class': 'form-select'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'order_in_contest': forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
        }
    
    def __init__(self, *args, **kwargs):
        super(ContestProblemForm, self).__init__(*args, **kwargs)
        # Only show problems created by the user or that are publicly available
        self.fields['problem'].queryset = Problem.objects.all().order_by('name')

# Create a formset for ContestProblem inline forms
ContestProblemFormSet = inlineformset_factory(
    Contest, 
    ContestProblem,
    form=ContestProblemForm,
    extra=1,  # Number of empty forms to display
    can_delete=True  # Allow removing problems from contest
)
