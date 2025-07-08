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
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
import json
from django.views import View
from problems.models import Problem # Assuming Problem model
from contests.models import Contest, ContestProblem, ContestSubmission # Import contest models
from .tasks import evaluate_contest_submission_task, evaluate_submission_task
from django.views.decorators.http import require_POST, require_GET
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

# This view will replace your ContestSubmissionCreateAPIView for form submission
@login_required
@require_POST # Ensure only POST requests are accepted
def submit_contest_code(request, contest_id, problem_id):
    contest = get_object_or_404(Contest, id=contest_id)
    problem = get_object_or_404(Problem, id=problem_id)

    # --- Pre-submission Checks (Crucial!) ---
    # 1. Check if user is a participant
    if not contest.participants.filter(pk=request.user.pk).exists():
        messages.error(request, "You must be registered for this contest to submit code.")
        return redirect('contests:solve_contest_problem', contest_pk=contest_id, problem_pk=problem_id)
    
    # 2. Check if contest is active (not ended or upcoming)
    if not contest.is_active():
        if contest.is_ended():
            messages.error(request, "This contest has ended. Submissions are no longer accepted.")
        else: # Upcoming or Cancelled
            messages.error(request, "This contest is not active yet. Submissions are not allowed.")
        return redirect('contests:solve_contest_problem', contest_pk=contest_id, problem_pk=problem_id)

    # 3. Ensure the problem actually belongs to this contest
    contest_problem = get_object_or_404(ContestProblem, contest=contest, problem=problem)

    code = request.POST.get('code', '')
    language = request.POST.get('language', '')

    if not code.strip():
        messages.error(request, "Submission code cannot be empty.")
        return redirect('contests:solve_contest_problem', contest_pk=contest_id, problem_pk=problem_id)

    allowed_languages = ['python', 'cpp', 'java'] # Match your judge_core/judge.py
    if language not in allowed_languages:
        messages.error(request, f"Unsupported language: {language}. Please choose from Python, C++, or Java.")
        return redirect('contests:solve_contest_problem', contest_pk=contest_id, problem_pk=problem_id)

    try:
        # Create a new ContestSubmission instance
        submission = ContestSubmission.objects.create(
            participant=request.user,
            contest_problem=contest_problem, # Link to the ContestProblem instance
            code=code,
            language=language,
            status='pending', # Initial status
            # final_verdict, test_cases_passed, total_test_cases, execution_time, memory_used, judge_output will be set by judge
        )

        # Queue the evaluation task for contest submissions
        # IMPORTANT: You'll need a separate Celery task for ContestSubmissions
        # that updates ContestSubmission model, not Submission model.
        # Let's call it evaluate_contest_submission_task for clarity.
        evaluate_contest_submission_task.delay(submission.id)

        messages.success(request, "Your contest submission has been received and is pending evaluation.")
        
        # Redirect back to the same problem page to see the new submission in the list
        return redirect('contests:solve_contest_problem', contest_pk=contest_id, problem_pk=problem_id)

    except Exception as e:
        messages.error(request, f"An error occurred during submission: {e}")
        # Log the error properly in production
        print(f"Error in submit_contest_code: {e}")
        return redirect('contests:solve_contest_problem', contest_pk=contest_id, problem_pk=problem_id)


# Keep your ContestSubmissionStatusAPIView if you want to use it for polling
# Just ensure it's fetching from ContestSubmission and not Submission
class ContestSubmissionStatusAPIView(LoginRequiredMixin, View):
    """
    API endpoint to get the status of a specific contest submission.
    """
    def get(self, request, pk, *args, **kwargs):
        submission = get_object_or_404(ContestSubmission, pk=pk)
        
        if request.user != submission.participant and not request.user.is_staff and not request.user.is_superuser:
             return JsonResponse({'error': 'Not authorized to view this submission.'}, status=403)

        data = {
            'id': submission.id,
            'status': submission.status, # This will be 'pending', 'processing', or 'finished'
            'final_verdict': submission.final_verdict, # This will be 'pending_evaluation', 'accepted', 'wrong_answer', etc.
            'test_cases_passed': submission.test_cases_passed,
            'total_test_cases': submission.total_test_cases,
            'execution_time': submission.execution_time,
            'memory_used': submission.memory_used,
            'judge_output': submission.judge_output,
        }
        return JsonResponse(data)



# --- NEW VIEW: contest_submission_detail_view ---
@login_required
def contest_submission_detail_view(request, submission_id):
    """
    Displays the details of a specific contest submission.
    """
    submission = get_object_or_404(ContestSubmission, pk=submission_id)

    # Ensure the user is authorized to view this submission
    # Only the participant, or staff/admin, should be able to view it.
    if request.user != submission.participant and not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "You are not authorized to view this contest submission.")
        # Redirect to a safe place, e.g., contest problems page or contest list
        return redirect('contests:solve_contest_problem', contest_pk=submission.contest_problem.contest.id, problem_pk=submission.contest_problem.problem.id)

    context = {
        'submission': submission,
        'is_contest_submission': True, # Flag for template to differentiate
        # You might want to pass problem and contest details directly for convenience
        'problem': submission.contest_problem.problem,
        'contest': submission.contest_problem.contest,
    }
    # You'll need to create a new template for this, e.g., 'submissions/contest_submission_detail.html'
    return render(request, 'submissions/contest_submission_detail.html', context)
