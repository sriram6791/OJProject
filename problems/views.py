from django.shortcuts import render,get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Problem, Submission


# Create your views here.

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
