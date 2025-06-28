# leaderboard/views.py

from django.shortcuts import render
from django.db.models import Count, Q
from django.contrib.auth import get_user_model

from submissions.models import Submission # Correct import for Submission

def leaderboard_view(request):
    """
    Displays the top 10 users who solved the most unique problems.
    """
    User = get_user_model()

    top_users = User.objects.annotate(
        solved_problems_count=Count(
            'submissions__problem',  # This part was already correct
            filter=Q(submissions__final_verdict='accepted'), # <-- THIS IS THE LINE THAT NEEDS THE FIX: 'submissions' (plural)
            distinct=True
        )
    ).order_by('-solved_problems_count')[:10]

    context = {
        'top_users': top_users,
    }
    return render(request, 'leaderboard/leaderboard.html', context)