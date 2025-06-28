from django.shortcuts import render , redirect
from django.contrib import messages
from django.contrib.auth import login,logout,authenticate
from django.contrib.auth.decorators import login_required
from .froms import UserRegistrationForm,UserLoginForm
from .models import CustomUser
from submissions.models import Submission
# Create your views here.

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request,user)
            messages.success(request,f"Account Created successfully for {user.username}!")
            return redirect('home')
            
            
    else:
        form = UserRegistrationForm()
    
    return render(request,'users/register.html' , {'form':form})


def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request,data= request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username,password=password)
            
            if user is not None:
                login(request,user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('home') # Redirect to home page
            else:
                messages.error(request, "Invalid username/email or password.")
        else:
            messages.error(request, "Invalid username/email or password.") # Default error for form validation failure
    
    else:
        form = UserLoginForm()
    return render(request, 'users/login.html', {'form': form})

@login_required 
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home') # Redirect to home page after logout
    
    
@login_required
def profile_view(request):
    user = request.user
    total_submissions = Submission.objects.filter(user=user).count()
    accepted_submissions = Submission.objects.filter(user=user,final_verdict='accepted').count()
    
    solved_problems_count = Submission.objects.filter(
        user=user,
        final_verdict = 'accepted',
    ).values('problem').distinct().count()
    
    context = {
        'user_profile' : user,
        'total_submissions': total_submissions,
        'accepted_submissions':accepted_submissions,
        'solved_problems_count' : solved_problems_count,
    }
    
    return render(request,'users/profile.html',context)