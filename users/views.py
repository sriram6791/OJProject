# users/views.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password # To verify password for login with email/username
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView
from django.views import View
from django.http import HttpResponseRedirect

from .serializers import UserRegisterSerializer, UserLoginSerializer, UserProfileSerializer
from .models import CustomUser # Import CustomUser
from .forms import UserRegistrationForm, UserLoginForm

# Template-based views
def register_view(request):
    """
    Template-based view for user registration.
    """
    if request.method == 'POST':
        print("POST request received")  # Debug print
        print("POST data:", request.POST)  # Debug print
        form = UserRegistrationForm(request.POST)
        print("Form is valid:", form.is_valid())  # Debug print
        if form.is_valid():
            user = form.save()
            print("User created:", user.username)  # Debug print
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('users:login')
        else:
            print("Form errors:", form.errors)  # Debug print
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    """
    Template-based view for user login.
    """
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')  # Redirect to home page after login
        else:
            messages.error(request, 'Invalid username/email or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    """
    Template-based view for user logout.
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def profile_view(request):
    """
    Template-based view for user profile.
    Shows user statistics and recent submissions.
    """
    from django.db.models import Count, Q
    from submissions.models import Submission
    from django.contrib.auth import get_user_model

    User = get_user_model()
    
    # Get all user submissions
    user_submissions = Submission.objects.filter(user=request.user)
    
    # Count total submissions
    total_count = user_submissions.count()
    
    # Count accepted submissions (problems solved)
    accepted_count = user_submissions.filter(final_verdict='accepted').count()
    
    # Count unique accepted problems
    unique_accepted_problems = user_submissions.filter(
        final_verdict='accepted'
    ).values_list('problem', flat=True).distinct().count()
    
    # Calculate success rate
    success_rate = (accepted_count / total_count * 100) if total_count > 0 else 0
    
    # Get recent submissions (last 10)
    recent_submissions = user_submissions.select_related('problem')[:10]
    
    # Calculate user rank
    # Get all users with their solved problem counts
    users_with_solved_counts = User.objects.annotate(
        solved_problems_count=Count(
            'submissions__problem',
            filter=Q(submissions__final_verdict='accepted'),
            distinct=True
        )
    ).order_by('-solved_problems_count')
    
    # Find the current user's rank
    user_rank = None
    for index, user in enumerate(users_with_solved_counts, start=1):
        if user.id == request.user.id:
            user_rank = index
            break
    
    context = {
        'user': request.user,
        'user_submissions': {
            'total_count': total_count,
            'accepted_count': unique_accepted_problems,  # Using unique problems count
            'success_rate': success_rate,
        },
        'user_rank': user_rank,
        'recent_submissions': recent_submissions,
    }
    
    return render(request, 'users/profile.html', context)

# API Views
class UserRegisterAPIView(APIView):
    """
    API endpoint for user registration.
    """
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "message": "User registered successfully.",
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "token": token.key
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginAPIView(APIView):
    """
    API endpoint for user login. Returns authentication token.
    """
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username_or_email = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = None
            # Try authenticating with username
            try:
                user = CustomUser.objects.get(username=username_or_email)
                if not check_password(password, user.password):
                    user = None # Password mismatch
            except CustomUser.DoesNotExist:
                pass

            # If not found by username, try authenticating with email
            if user is None:
                try:
                    user = CustomUser.objects.get(email=username_or_email)
                    if not check_password(password, user.password):
                        user = None # Password mismatch
                except CustomUser.DoesNotExist:
                    pass

            if user is not None:
                # Manually log in the user to establish session (optional for token auth, but good practice)
                login(request, user)
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    "message": "Login successful.",
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "token": token.key
                }, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLogoutAPIView(APIView):
    """
    API endpoint for user logout. Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Delete the user's authentication token
        if request.user.auth_token:
            request.user.auth_token.delete()
        logout(request) # Also log out from session if session auth is used
        return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)

class UserProfileAPIView(APIView):
    """
    API endpoint for retrieving and updating user profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True) # partial=True allows partial updates
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Add this view for admin to authorize problem setters
class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin that tests whether the user is an admin
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'admin'
    
    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to access this page. This page is only accessible to administrators.")
        return redirect('home')

class AuthorizeProblemSettersView(AdminRequiredMixin, ListView):
    """
    View for admin to authorize problem setters
    """
    model = CustomUser
    template_name = 'users/authorize_problem_setters.html'
    context_object_name = 'problem_setters'
    
    def get_queryset(self):
        # Only return users with the role of problem_setter
        return CustomUser.objects.filter(role='problem_setter')
    
    def post(self, request, *args, **kwargs):
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        if user_id and action in ['authorize', 'deauthorize']:
            try:
                user = CustomUser.objects.get(id=user_id, role='problem_setter')
                if action == 'authorize':
                    user.is_authorized = True
                    messages.success(request, f'User {user.username} has been authorized as a problem setter.')
                else:
                    user.is_authorized = False
                    messages.success(request, f'User {user.username} has been deauthorized as a problem setter.')
                user.save()
            except CustomUser.DoesNotExist:
                messages.error(request, 'User not found or not a problem setter.')
        
        return HttpResponseRedirect(request.path_info)
