from django import forms
from .models import Problem, TestCase
from django.forms import inlineformset_factory

class ProblemForm(forms.ModelForm):
    """Form for creating and editing problems"""
    
    class Meta:
        model = Problem
        fields = ['name', 'statement', 'difficulty']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter problem name'}),
            'statement': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Enter the full problem description including background, constraints, and examples'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
        }
        
class TestCaseForm(forms.ModelForm):
    """Form for creating and editing test cases"""
    
    class Meta:
        model = TestCase
        fields = ['input_data', 'expected_output', 'is_hidden', 'order']
        widgets = {
            'input_data': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter input data'}),
            'expected_output': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter expected output'}),
            'is_hidden': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
        }

# Create a formset for TestCase inline forms
TestCaseFormSet = inlineformset_factory(
    Problem, 
    TestCase,
    form=TestCaseForm,
    extra=2,  # Number of empty forms to display
    can_delete=True  # Allow deleting test cases
)
