from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Case, When, IntegerField
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
from django.conf import settings
from django.views.decorators.http import require_http_methods
import requests
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
        # Check if the user is a problem setter and is authorized
        if request.user.role == 'problem_setter' and not request.user.is_authorized:
            messages.warning(request, "You need to be authorized by an admin to create problems. Please contact an administrator.")
            return redirect('creator:portal')
        
        form = ProblemForm()
        formset = TestCaseFormSet(prefix='testcases')
        
        return render(request, 'problems/create.html', {
            'form': form,
            'formset': formset,
            'title': 'Create Problem'
        })
    
    def post(self, request):
        # Check if the user is a problem setter and is authorized
        if request.user.role == 'problem_setter' and not request.user.is_authorized:
            messages.warning(request, "You need to be authorized by an admin to create problems. Please contact an administrator.")
            return redirect('creator:portal')
            
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
        # Check if the user is a problem setter and is authorized
        if request.user.role == 'problem_setter' and not request.user.is_authorized:
            messages.warning(request, "You need to be authorized by an admin to edit problems. Please contact an administrator.")
            return redirect('creator:portal')
            
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
        # Check if the user is a problem setter and is authorized
        if request.user.role == 'problem_setter' and not request.user.is_authorized:
            messages.warning(request, "You need to be authorized by an admin to edit problems. Please contact an administrator.")
            return redirect('creator:portal')
            
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
        # Custom ordering: easy (1) -> medium (2) -> hard (3)
        problems = problems.annotate(
            difficulty_order=Case(
                When(difficulty='easy', then=1),
                When(difficulty='medium', then=2),
                When(difficulty='hard', then=3),
                output_field=IntegerField()
            )
        ).order_by('difficulty_order')
    elif sort_by == 'difficulty_desc':
        # Custom ordering: hard (3) -> medium (2) -> easy (1)
        problems = problems.annotate(
            difficulty_order=Case(
                When(difficulty='easy', then=1),
                When(difficulty='medium', then=2),
                When(difficulty='hard', then=3),
                output_field=IntegerField()
            )
        ).order_by('-difficulty_order')
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


@csrf_exempt
@require_http_methods(["POST"])
def ai_assistant_chat(request):
    """
    AI Assistant endpoint for coding-specific questions
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        problem_context = data.get('problem_context', '')
        code = data.get('code', '')
        action_type = data.get('action_type', 'chat')  # chat, analyze, explain, dry_run
        language = data.get('language', '')
        test_cases = data.get('test_cases', [])
        
        # Handle problem context - support both old string format and new object format
        if isinstance(problem_context, dict):
            problem_name = problem_context.get('name', 'Unknown Problem')
            problem_statement = problem_context.get('statement', 'No description available')
            problem_difficulty = problem_context.get('difficulty', 'Unknown')
            full_problem_context = f"""
**PROBLEM:** {problem_name} ({problem_difficulty.title()})
**DESCRIPTION:** {problem_statement}
"""
        else:
            # Fallback for old format
            problem_name = problem_context if problem_context else 'Unknown Problem'
            full_problem_context = f"**PROBLEM:** {problem_name}"
        
        if not user_message and action_type == 'chat':
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get API key from settings
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key:
            return JsonResponse({'error': 'AI Assistant is not configured'}, status=500)
        
        # Create specialized prompts based on action type
        if action_type == 'analyze':
            system_prompt = f"""🔍 **COMPETITIVE PROGRAMMING CODE ANALYZER**

You are an expert competitive programming mentor specializing in code analysis and optimization. Your task is to thoroughly analyze the submitted code for:

{full_problem_context}

**CODE TO ANALYZE:**
```{language}
{code}
```

**🎯 COMPREHENSIVE ANALYSIS FRAMEWORK:**

**1. CORRECTNESS AUDIT:**
   - ✅ Verify algorithm correctness for the specific problem
   - 🐛 Identify logical errors, off-by-one errors, or incorrect assumptions
   - 🎯 Check if solution handles all problem constraints properly
   - 📝 Validate input/output format compliance

**2. EDGE CASE VULNERABILITY ASSESSMENT:**
   - 🔬 Analyze boundary conditions (min/max values, empty inputs)
   - ⚠️ Check for integer overflow, array bounds violations
   - 🎲 Identify missing edge cases that could cause Wrong Answer
   - 💡 Suggest test cases that might break the current solution

**3. COMPLEXITY ANALYSIS:**
   - ⏱️ **Time Complexity:** Calculate Big-O notation with justification
   - 💾 **Space Complexity:** Analyze memory usage patterns
   - 📊 Compare against typical competitive programming time limits (1-2 seconds)
   - 🚀 Identify if optimization is needed for larger constraints

**4. OPTIMIZATION OPPORTUNITIES:**
   - 🎯 Suggest algorithmic improvements (better data structures, algorithms)
   - 🔧 Code-level optimizations (loop efficiency, unnecessary operations)
   - 📈 Performance improvements for competitive programming standards
   - 💡 Alternative approaches with better complexity

**5. CODE QUALITY & STYLE:**
   - 📝 Variable naming and code readability
   - 🔄 Code structure and modularity
   - ⚡ Potential runtime optimizations (avoid repeated calculations)

**OUTPUT FORMAT:**
Provide a structured analysis with specific, actionable feedback. Use emojis and clear sections. Be direct about issues and provide concrete suggestions for improvement. Focus on what matters most for competitive programming success.KEEP YOUR RESPONSES AS CONCISE AS POSSIBLE BE ON POINT , STRAIGHT FORWARD, GIVE SHORT EFFECTIVE RESPONSES"""

        elif action_type == 'explain':
            system_prompt = f"""📚 **COMPETITIVE PROGRAMMING CODE EXPLAINER**

You are an expert competitive programming tutor specializing in making complex algorithms understandable. Your mission is to explain the code solution for:

{full_problem_context}

**CODE TO EXPLAIN:**
```{language}
{code}
```

**🎯 COMPREHENSIVE EXPLANATION FRAMEWORK:**

**1. SOLUTION OVERVIEW:**
   - 🧠 **Core Algorithm:** Identify and name the main algorithmic approach
   - 🎯 **Problem Strategy:** Explain how this approach solves the specific problem
   - 💡 **Key Insight:** What's the main idea that makes this solution work?
   - 📊 **Complexity Summary:** Quick overview of time/space complexity

**2. STEP-BY-STEP CODE BREAKDOWN:**
   - 🔍 **Initialization Phase:** Explain variable declarations and input handling
   - ⚙️ **Core Logic:** Break down the main algorithm section by section
   - 🔄 **Loop Analysis:** Explain what each loop accomplishes and why
   - 📤 **Output Generation:** How the final result is computed and formatted

**3. DATA STRUCTURES & TECHNIQUES:**
   - 📦 **Data Structures Used:** Arrays, lists, maps, etc. and why they're chosen
   - 🎛️ **Key Functions/Methods:** Explain important built-in functions or custom logic
   - 🔧 **Programming Techniques:** Sorting, searching, dynamic programming patterns, etc.

**4. ALGORITHM WALKTHROUGH:**
   - 📝 **Trace Through Logic:** Show how the algorithm processes data
   - 🎲 **Example Execution:** If possible, trace through with sample input
   - 🧩 **Connect to Problem:** Explain how each part relates to solving the original problem

**5. LEARNING INSIGHTS:**
   - 💡 **Why This Approach:** Explain why this solution is effective
   - 📈 **Pattern Recognition:** What algorithmic patterns or concepts are used
   - 🎯 **When to Use:** In what types of problems would similar approaches work

**OUTPUT STYLE:**
Use clear, educational language with examples. Make complex concepts accessible. Use emojis and formatting to enhance readability. Focus on building understanding, not just describing what the code does.KEEP YOUR RESPONSES AS CONCISE AS POSSIBLE BE ON POINT , STRAIGHT FORWARD, GIVE SHORT EFFECTIVE RESPONSES"""

        elif action_type == 'dry_run':
            test_case_info = ""
            if test_cases:
                test_case_info = f"\n**SAMPLE TEST CASE:**\n{test_cases}"
            
            system_prompt = f"""🔬 **COMPETITIVE PROGRAMMING DRY RUN DEBUGGER**

You are an expert debugging mentor for competitive programming. Your task is to perform a detailed execution trace of the code for:

{full_problem_context}

**CODE TO DRY RUN:**
```{language}
{code}
```
{test_case_info}

**🎯 COMPREHENSIVE DRY RUN PROTOCOL:**

**1. EXECUTION SETUP:**
   - 📥 **Input Analysis:** Break down the input format and values
   - 📋 **Variable Initialization:** Show initial state of all variables
   - 🎯 **Expected Output:** State what the correct output should be

**2. STEP-BY-STEP EXECUTION TRACE:**
   - 🔢 **Line-by-Line Execution:** Trace through each significant line
   - 📊 **Variable State Tracking:** Show variable values after each major operation
   - 🔄 **Loop Iterations:** Detail what happens in each loop iteration
   - 🎛️ **Function Calls:** Trace through any function calls or recursive operations

**3. INTERMEDIATE RESULTS:**
   - 📈 **Calculation Steps:** Show mathematical operations and their results
   - 🏗️ **Data Structure Changes:** Track arrays, lists, or other structure modifications
   - 🔍 **Conditional Evaluations:** Show which if/else branches are taken and why

**4. BUG DETECTION & VALIDATION:**
   - 🐛 **Error Identification:** Spot logical errors, infinite loops, or wrong calculations
   - ⚠️ **Warning Signs:** Identify potential issues even if not immediately fatal
   - ✅ **Output Verification:** Compare actual output with expected result
   - 🎯 **Correctness Check:** Verify if the solution addresses the problem correctly

**5. DEBUGGING INSIGHTS:**
   - 💡 **Issue Diagnosis:** If bugs found, explain what went wrong and why
   - 🔧 **Fix Suggestions:** Provide specific recommendations for corrections
   - 🎲 **Alternative Test Cases:** Suggest other inputs that might reveal issues
   - 📝 **Verification Strategy:** How to test the fix

**OUTPUT FORMAT:**
Present the dry run in a clear, tabular or step-by-step format. Use code blocks for variable states. Be thorough but organized. Highlight any issues found with clear explanations and actionable fixes.KEEP YOUR RESPONSES AS CONCISE AS POSSIBLE BE ON POINT , STRAIGHT FORWARD, GIVE SHORT EFFECTIVE RESPONSES"""

        else:  # Default chat
            system_prompt = f"""💬 **COMPETITIVE PROGRAMMING CODING ASSISTANT**

You are an expert competitive programming mentor and coding assistant. You specialize in helping programmers solve algorithmic challenges and improve their competitive programming skills.

**🎯 YOUR EXPERTISE COVERS:**
- 🧮 **Algorithms:** Sorting, searching, graph algorithms, dynamic programming, greedy algorithms
- 📊 **Data Structures:** Arrays, trees, graphs, heaps, hash tables, segment trees, etc.
- 🔧 **Debugging:** Logic errors, performance issues, edge cases
- ⚡ **Optimization:** Time/space complexity improvements, code efficiency
- 📝 **Problem Solving:** Approach strategies, pattern recognition, solution techniques
- 🎯 **Competitive Programming:** Contest strategies, common pitfalls, best practices

**📋 CURRENT PROBLEM CONTEXT:** 
{full_problem_context}

**🚫 STRICT BOUNDARIES:**
- ONLY programming, algorithms, data structures, and competitive programming topics
- NO general knowledge, personal questions, or non-technical subjects
- Focus on educational guidance and hints

**🎓 TEACHING APPROACH:**
- Provide hints and guidance to promote learning
- Explain concepts clearly with examples
- Help with debugging when code is provided
- Encourage best practices for competitive programming

**❌ NON-PROGRAMMING QUERY RESPONSE:**
"I'm a specialized competitive programming assistant. I can only help with coding, algorithms, data structures, debugging, and programming concepts. Please ask me about your coding challenges, algorithm questions, or programming techniques!"

- If user asks for code for the question you need to give the code in this format only so that our judge accepts properly.
example : hello world problem
python:
print("hello world")

cpp:
#include <iostream>
using namespace std;
int main() 
cout << "hello world" << endl;
return 0;

java:
public class Solution 
    public static void main(String[] args) 
        System.out.println("hello world");
    
with proper correct syntax and brackets For java try to maintain Solution class properly
**💡 USER'S QUESTION:** {user_message}

**Response Guidelines:** Be encouraging, educational, and focused on helping them grow as a competitive programmer. Provide specific, actionable advice tailored to their skill level and question.KEEP YOUR RESPONSES AS CONCISE AS POSSIBLE BE ON POINT , STRAIGHT FORWARD, GIVE SHORT EFFECTIVE RESPONSES"""

        # Prepare the API request
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": system_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.8,
                "topK": 40,
                "maxOutputTokens": 2048,  # Increased for detailed analysis
            }
        }
        
        # Make request to Gemini API
        response = requests.post(
            api_url,
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            return JsonResponse({'error': 'AI service temporarily unavailable'}, status=500)
        
        result = response.json()
        
        # Extract AI response
        ai_response = "Sorry, I couldn't generate a response. Please try again."
        if (result.get('candidates') and 
            len(result['candidates']) > 0 and 
            result['candidates'][0].get('content') and 
            result['candidates'][0]['content'].get('parts') and 
            len(result['candidates'][0]['content']['parts']) > 0):
            ai_response = result['candidates'][0]['content']['parts'][0]['text']
        elif result.get('error'):
            return JsonResponse({'error': f"AI Error: {result['error']['message']}"}, status=500)
        
        return JsonResponse({'response': ai_response})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except requests.RequestException as e:
        return JsonResponse({'error': 'AI service connection failed'}, status=500)
    except Exception as e:
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)
