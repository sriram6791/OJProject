from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from problems.models import Problem # Import Problem model
from .models import Submission # Import Submission model
from .tasks import evaluate_submission_task # Import the Celery task
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import redirect, get_object_or_404

@login_required
def submit_code_view(request, problem_id):
    """
    Handles POST requests for code submission.
    Creates a new Submission object and queues it for asynchronous evaluation.
    """
    if request.method == 'POST':
        try:
            problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            messages.error(request, "Problem not found.")
            return redirect('problems:list')

        code = request.POST.get('code', '')
        language = request.POST.get('language', '')

        if not code.strip():
            messages.error(request, "Submission cannot be empty.")
            return redirect('problems:detail', problem_id=problem_id)

        # Validate language against allowed choices (optional, but good practice)
        allowed_languages = ['python', 'cpp', 'java'] # Must match keys in judge_core/judge.py
        if language not in allowed_languages:
            messages.error(request, "Unsupported language selected.")
            return redirect('problems:detail', problem_id=problem_id)

        # Create a new submission instance
        submission = Submission.objects.create(
            user=request.user,
            problem=problem,
            code=code,
            language=language,
            status='pending',
            final_verdict='pending'
        )

        # Queue the evaluation task using Celery
        evaluate_submission_task.delay(submission.id) # .delay() sends task to broker

        messages.success(request, "Your submission has been received and is pending evaluation.")
        return redirect('problems:detail', problem_id=problem_id)
    else:
        messages.error(request, "Invalid request method.")
        return redirect('problems:list')


@require_GET
@login_required # Only logged-in users can check status
def get_submission_status_api(request, submission_id):
    """
    API endpoint to get the status and verdict of a single submission.
    """
    try:
        submission = Submission.objects.get(id=submission_id)
        # Ensure user can only check their own submissions or if they are staff/admin
        if request.user != submission.user and not request.user.is_staff and not request.user.is_admin:
            return JsonResponse({'error': 'Not authorized'}, status=403)

        data = {
            'id': submission.id,
            'status': submission.status,
            'final_verdict': submission.final_verdict,
            'passed_test_cases': submission.passed_test_cases,
            'total_test_cases': submission.total_test_cases,
            'execution_time': submission.execution_time,
            'memory_used': submission.memory_used,
            'error_message': submission.error_message,
        }
        return JsonResponse(data)
    except Submission.DoesNotExist:
        return JsonResponse({'error': 'Submission not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
# TODO: Add a view for submission detail page if you want to show individual submission with full code, error messages etc.
# def submission_detail_view(request, submission_id):
#     submission = get_object_or_404(Submission, id=submission_id)
#     # Ensure only the submitting user or admin can view
#     if request.user != submission.user and not request.user.is_staff and not request.user.is_admin:
#         messages.error(request, "You are not authorized to view this submission.")
#         return redirect('home')
#     return render(request, 'submissions/submission_detail.html', {'submission': submission})


@login_required
def submission_detail_view(request,submission_id):
    submission = get_object_or_404(Submission,id = submission_id)
    
    if request.user != submission.user and \
        not request.user.is_staff and \
            request.user.role not in ['problem_setter','admin']:
        messages.error(request,"You are not authorized to view this submission.")
        return redirect('home')
    
    context = {
        'submission': submission,
    }
    
    return render(request,'submissions/submission_detail.html',context)