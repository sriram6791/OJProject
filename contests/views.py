from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages # Import messages for feedback
from django.contrib.auth.decorators import login_required # For function-based views
from django.utils.decorators import method_decorator # For class-based views with decorators
from .models import Contest, ContestProblem, ContestSubmission # Import ContestProblem, ContestSubmission
from django.conf import settings # Needed if you access settings like AUTH_USER_MODEL directly
# from problems.models import Problem # You'll need this when you actually display problems
from problems.models import Problem
# --- Existing Views (Keep these) ---
class ContestListView(View):
    """
    Displays a list of all contests, with search and pagination.
    """
    def get(self, request, *args, **kwargs):
        contests_list = Contest.objects.all()

        query = request.GET.get('q')
        if query:
            contests_list = contests_list.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            ).distinct()

        paginator = Paginator(contests_list, 9)
        page_number = request.GET.get('page')

        try:
            contests = paginator.page(page_number)
        except PageNotAnInteger:
            contests = paginator.page(1)
        except EmptyPage:
            contests = paginator.page(paginator.num_pages)

        context = {
            'contests': contests,
            'is_paginated': contests.has_other_pages(),
            'page_obj': contests,
            'query': query,
        }
        return render(request, 'contests/contests.html', context)


class ContestDetailView(View):
    """
    Displays details for a single contest.
    """
    def get(self, request, pk, *args, **kwargs):
        contest = get_object_or_404(Contest, pk=pk)

        is_participant = False
        if request.user.is_authenticated:
            is_participant = contest.participants.filter(pk=request.user.pk).exists()

        context = {
            'contest': contest,
            'is_participant': is_participant,
        }
        return render(request, 'contests/contest_detail.html', context)

# --- NEW Placeholder Views to resolve NoReverseMatch ---

@method_decorator(login_required, name='dispatch') # Ensures user is logged in
class ContestRegisterView(View):
    """
    Handles user registration for a contest.
    """
    def post(self, request, pk, *args, **kwargs):
        contest = get_object_or_404(Contest, pk=pk)
        
        # Check if contest is upcoming or active
        if contest.is_upcoming() or contest.is_active():
            # Add the current user to the participants ManyToMany field
            if not contest.participants.filter(pk=request.user.pk).exists():
                contest.participants.add(request.user)
                messages.success(request, f"Successfully registered for {contest.name}!")
            else:
                messages.info(request, f"You are already registered for {contest.name}.")
        else:
            messages.error(request, f"Cannot register for {contest.name}. It is not upcoming or active.")
        
        return redirect('contests:detail', pk=pk)


class ContestLeaderboardView(View):
    """
    Displays the leaderboard for a specific contest.
    """
    def get(self, request, pk, *args, **kwargs):
        contest = get_object_or_404(Contest, pk=pk)
        
        # Import necessary Django modules
        from django.db.models import Count, Max, Q, Case, When, IntegerField
        from django.db.models.functions import Coalesce
        
        # First, get a distinct list of problems solved by each participant
        # This ensures we only count each problem once per user
        distinct_solved_problems = ContestSubmission.objects.filter(
            contest_problem__contest=contest,
            final_verdict='accepted'
        ).values(
            'participant', 
            'contest_problem__problem'
        ).distinct()
        
        # Create a subquery to count distinct solved problems
        from django.db.models import Subquery, OuterRef
        
        # Get all users who submitted at least one solution to this contest
        user_submissions = ContestSubmission.objects.filter(
            contest_problem__contest=contest
        ).values(
            'participant', 
            'participant__username'
        ).annotate(
            # Count distinct problems solved by each user
            problems_solved=Count(
                'contest_problem__problem', 
                filter=Q(final_verdict='accepted'), 
                distinct=True
            ),
            total_count=Count('id'),
            last_submission_time=Max('submitted_at')
        ).order_by('-problems_solved', 'last_submission_time')
        
        # Create a leaderboard list
        leaderboard_data = []
        for entry in user_submissions:
            leaderboard_data.append({
                'user': {
                    'id': entry['participant'],
                    'username': entry['participant__username']
                },
                'score': entry['problems_solved'],  # Changed from accepted_count to problems_solved
                'total_submissions': entry['total_count'],
                'last_submission_time': entry['last_submission_time']
            })

        context = {
            'contest': contest,
            'leaderboard_data': leaderboard_data,
        }
        return render(request, 'contests/contest_leaderboard.html', context)
    
    
# --- NEW VIEW: ContestProblemSolveView ---
@method_decorator(login_required, name='dispatch')
class ContestProblemSolveView(View):
    """
    Displays the contest problem solving interface.
    Includes contest problems list, current problem statement, and submission area.
    """
    def get(self, request, contest_pk, problem_pk=None, *args, **kwargs):
        contest = get_object_or_404(Contest, pk=contest_pk)

        # Check if the user is a participant
        if not contest.participants.filter(pk=request.user.pk).exists():
            messages.warning(request, f"You must be registered for '{contest.name}' to access its problems.")
            return redirect('contests:detail', pk=contest_pk)
        
        # Check if the contest is active
        if not contest.is_active():
            # If contest is not active, but has ended, allow viewing problems/submissions
            if contest.is_ended():
                messages.info(request, f"'{contest.name}' has ended. You can review problems and your past submissions.")
            else: # Upcoming or Cancelled
                messages.error(request, f"'{contest.name}' is not active yet. Please wait for the contest to start.")
                return redirect('contests:detail', pk=contest_pk)

        # Get all problems for this contest, ordered by order_in_contest
        contest_problems = ContestProblem.objects.filter(contest=contest).order_by('order_in_contest')
        
        current_problem = None
        if problem_pk:
            # Get the specific problem if problem_pk is provided
            current_problem = get_object_or_404(Problem, pk=problem_pk)
            # Ensure the requested problem actually belongs to this contest
            if not ContestProblem.objects.filter(contest=contest, problem=current_problem).exists():
                messages.error(request, "The requested problem is not part of this contest.")
                # Redirect to the default solve page for the contest, which will load the first problem
                return redirect('contests:solve_contest_problem_default', contest_pk=contest_pk) 
        elif contest_problems.exists():
            # If no problem_pk, default to the first problem in the contest
            current_problem = contest_problems.first().problem
        else:
            # Handle case where there are no problems in the contest
            messages.info(request, "This contest currently has no problems available.")
            current_problem = None # Ensure current_problem is explicitly None if no problems
        
        # Fetch user's submissions for this contest (all problems for the sidebar status)
        user_contest_submissions = []
        current_problem_submissions = []
        if request.user.is_authenticated:
            # All user submissions for this contest (for the sidebar status indicators)
            user_contest_submissions = ContestSubmission.objects.filter(
                participant=request.user,
                contest_problem__contest=contest
            ).order_by('-submitted_at')
            
            # Submissions for the current problem only (for the submissions list display)
            if current_problem:
                current_problem_submissions = ContestSubmission.objects.filter(
                    participant=request.user,
                    contest_problem__contest=contest,
                    contest_problem__problem=current_problem
                ).order_by('-submitted_at')

        context = {
            'contest': contest,
            'contest_problems': contest_problems, # List of ContestProblem objects
            'current_problem': current_problem, # The actual Problem object
            'user_contest_submissions': user_contest_submissions, # All submissions for sidebar
            'current_problem_submissions': current_problem_submissions, # Current problem submissions for list
            'now': timezone.now(), # Pass current time for timer calculation in template
        }
        return render(request, 'contests/contest_problem_solve.html', context)
