from django.shortcuts import render
from django.db.models import Count,Q
from django.contrib.auth import get_user_model

# Create your views here.

from problems.models import Problem, Submission

def leaderboard_view(request):
    User = get_user_model()
    
    top_users = User.objects.annotate(
        solved_problems_count = Count('submission__problem',
                                      filter=Q(submission__final_verdict = 'accept'),
                                      distinct=True)
    ).order_by('-solved_problems_count')[:10]
    
    context = {
        'top_users': top_users,
    }
    
    return render(request,'leaderboard/leaderboard.html',context)