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
        
        # You'll need to fetch and process submission data here
        # For now, just a placeholder.
        leaderboard_data = [] # Example: [{'user': 'user1', 'score': 150}, ...]

        context = {
            'contest': contest,
            'leaderboard_data': leaderboard_data,
        }
        # You'll create a contests/contest_leaderboard.html template next
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
        
        # Fetch user's submissions for this specific contest and problem
        user_contest_submissions = []
        if request.user.is_authenticated and current_problem:
            user_contest_submissions = ContestSubmission.objects.filter(
                participant=request.user,
                contest_problem__contest=contest,
                contest_problem__problem=current_problem
            ).order_by('-submitted_at') # Order by most recent first

        context = {
            'contest': contest,
            'contest_problems': contest_problems, # List of ContestProblem objects
            'current_problem': current_problem, # The actual Problem object
            'user_contest_submissions': user_contest_submissions,
            'now': timezone.now(), # Pass current time for timer calculation in template
        }
        return render(request, 'contests/contest_problem_solve.html', context)
