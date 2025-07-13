from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Problem, TestCase
from submissions.models import Submission
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from judge_core.judge import evaluate_with_custom_input
import json
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from .forms import ProblemForm, TestCaseFormSet


class ProblemSetterRequiredMixin(UserPassesTestMixin):
    """
    Mixin that tests whether the user is a problem setter or admin
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['problem_setter', 'admin']
    
    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to access this page. Only problem setters can create and edit problems.")
        return redirect('home')


class CreateProblemView(ProblemSetterRequiredMixin, View):
    """
    View for creating a new problem
    """
    def get(self, request):
        form = ProblemForm()
        formset = TestCaseFormSet(prefix='testcases')
        
        return render(request, 'problems/create.html', {
            'form': form,
            'formset': formset,
            'title': 'Create Problem'
        })
    
    def post(self, request):
        form = ProblemForm(request.POST)
        formset = TestCaseFormSet(request.POST, prefix='testcases')
        
        print("Form valid:", form.is_valid())
        print("Formset valid:", formset.is_valid())
        
        if not form.is_valid():
            print("Form errors:", form.errors)
        
        if not formset.is_valid():
            print("Formset errors:", formset.errors)
        
        if form.is_valid() and formset.is_valid():
            problem = form.save(commit=False)
            problem.created_by = request.user
            problem.save()
            
            # Save test cases
            instances = formset.save(commit=False)
            for instance in instances:
                instance.problem = problem
                instance.save()
            
            # Delete marked test cases
            for obj in formset.deleted_objects:
                obj.delete()
            
            messages.success(request, f"Problem '{problem.name}' created successfully!")
            return redirect('problems:detail', problem_id=problem.id)
        
        return render(request, 'problems/create.html', {
            'form': form,
            'formset': formset,
            'title': 'Create Problem'
        })


class EditProblemView(ProblemSetterRequiredMixin, View):
    """
    View for editing an existing problem
    """
    def get(self, request, problem_id):
        problem = get_object_or_404(Problem, id=problem_id)
        
        # Check if user is the creator or an admin
        if problem.created_by != request.user and request.user.role != 'admin':
            messages.error(request, "You can only edit problems that you created.")
            return redirect('problems:detail', problem_id=problem.id)
        
        form = ProblemForm(instance=problem)
        formset = TestCaseFormSet(instance=problem, prefix='testcases')
        
        return render(request, 'problems/edit.html', {
            'form': form,
            'formset': formset,
            'problem': problem,
            'title': f'Edit Problem: {problem.name}'
        })
    
    def post(self, request, problem_id):
        problem = get_object_or_404(Problem, id=problem_id)
        
        # Check if user is the creator or an admin
        if problem.created_by != request.user and request.user.role != 'admin':
            messages.error(request, "You can only edit problems that you created.")
            return redirect('problems:detail', problem_id=problem.id)
        
        form = ProblemForm(request.POST, instance=problem)
        formset = TestCaseFormSet(request.POST, instance=problem, prefix='testcases')
        
        if form.is_valid() and formset.is_valid():
            problem = form.save()
            formset.save()
            
            messages.success(request, f"Problem '{problem.name}' updated successfully!")
            return redirect('problems:detail', problem_id=problem.id)
        
        return render(request, 'problems/edit.html', {
            'form': form,
            'formset': formset,
            'problem': problem,
            'title': f'Edit Problem: {problem.name}'
        })

def problem_list_view(request):
    problems = Problem.objects.all()
    
    # Filtering
    difficulty = request.GET.get('difficulty')
    if difficulty and difficulty != 'all':
        problems = problems.filter(difficulty=difficulty)
        
    
    # --- Searching ---
    search_query = request.GET.get('q')
    if search_query:
        problems = problems.filter(
            Q(name__icontains=search_query) |
            Q(statement__icontains=search_query)
        )
        
    
    # Sorting
    sort_by = request.GET.get('sort_by','name')
    if sort_by == 'difficulty_asc':
        problems = problems.order_by('difficulty')
    elif sort_by == 'difficulty_desc':
        problems = problems.order_by('-difficulty')
    elif sort_by == 'created_at_asc':
        problems = problems.order_by('created_at')
    elif sort_by == 'created_at_desc':
        problems = problems.order_by('-created_at')
    else: # Default to sorting by name ascending
        problems = problems.order_by('name')
        
    paginator = Paginator(problems,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'difficulties': [choice[0] for choice in Problem.difficulty_choices], # Pass choices for dropdown
        'selected_difficulty': difficulty,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'problems/problem_list.html', context)

def problem_detail_view(request, problem_id):

    problem = get_object_or_404(Problem, id=problem_id)
    
    user_submissions = []
    if request.user.is_authenticated:
        # Fetch submissions only for the logged-in user for this problem
        user_submissions = Submission.objects.filter(user=request.user, problem=problem).order_by('-submitted_at')
    
    context = {
        'problem': problem,
        'user_submissions': user_submissions,
        'language_choices': ['Python', 'C++', 'Java'], # Hardcoded for now
    }
    return render(request, 'problems/problem_detail.html', context)

@csrf_exempt  # For simplicity. In production, use proper CSRF protection
def test_with_custom_input(request):
    print("Received request for custom input testing")
    if request.method != 'POST':
        print(f"Invalid method: {request.method}")
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        print("Received data:", data)
        code = data.get('code')
        input_data = data.get('input', '')
        language = data.get('language', '').lower()
        print(f"Processing: language={language}, input_length={len(input_data) if input_data else 0}")
        
        if not code or not language:
            return JsonResponse({'error': 'Code and language are required'}, status=400)
            
        result = evaluate_with_custom_input(code, input_data, language)
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
