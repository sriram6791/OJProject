from django.contrib import admin
from .models import Contest, ContestProblem, ContestSubmission
from problems.models import Problem # You might need this for raw_id_fields if Problem is complex

# --- Inline for ContestProblem to manage problems directly from the Contest admin page ---
class ContestProblemInline(admin.TabularInline):
    # This inline allows you to add/edit ContestProblem instances
    # directly when editing a Contest.
    model = ContestProblem
    extra = 1 # Number of empty forms to display
    raw_id_fields = ('problem',) # Use a raw ID field for the problem ForeignKey for better performance with many problems
    fields = ('problem', 'points', 'order_in_contest',) # Fields to display in the inline form


# --- Contest Admin Configuration ---
@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'start_time',
        'end_time',
        'get_duration', # Custom method to display duration
        'status',
        'created_by',
        'created_at',
    )
    list_filter = ('status', 'created_at', 'start_time', 'end_time')
    search_fields = ('name', 'description')
    date_hierarchy = 'start_time' # Adds a date-based navigation to the top of the list
    ordering = ('-start_time',) # Default ordering
    
    # Use raw_id_fields for ForeignKey to CustomUser for better performance
    # especially if you have many users. It shows an input field with a lookup button.
    raw_id_fields = ('created_by',) 

    # Inlines allow you to edit related objects on the same page
    inlines = [ContestProblemInline,]

    # Custom action to update contest status (e.g., set to Active)
    # This is an example, you might want more sophisticated status management
    actions = ['make_active', 'make_upcoming', 'make_ended']

    def make_active(self, request, queryset):
        rows_updated = queryset.update(status='active')
        self.message_user(request, f'{rows_updated} contests marked as Active.')
    make_active.short_description = "Mark selected contests as Active"

    def make_upcoming(self, request, queryset):
        rows_updated = queryset.update(status='upcoming')
        self.message_user(request, f'{rows_updated} contests marked as Upcoming.')
    make_upcoming.short_description = "Mark selected contests as Upcoming"

    def make_ended(self, request, queryset):
        rows_updated = queryset.update(status='ended')
        self.message_user(request, f'{rows_updated} contests marked as Ended.')
    make_ended.short_description = "Mark selected contests as Ended"


# --- ContestProblem Admin Configuration (if you want to manage it separately too) ---
# If you primarily manage ContestProblem through ContestInline, this standalone admin might be less used.
# But it's good to have for direct access.
@admin.register(ContestProblem)
class ContestProblemAdmin(admin.ModelAdmin):
    list_display = ('contest', 'problem', 'order_in_contest', 'points')
    list_filter = ('contest', 'problem__difficulty') # Filter by contest and problem difficulty
    search_fields = ('contest__name', 'problem__name')
    ordering = ('contest__name', 'order_in_contest')
    raw_id_fields = ('contest', 'problem') # Use raw ID fields for ForeignKeys


# --- ContestSubmission Admin Configuration ---
@admin.register(ContestSubmission)
class ContestSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'participant',
        'contest_problem',
        'status',
        'score',
        'submitted_at',
        'test_cases_passed',
        'total_test_cases'
    )
    list_filter = (
        'status',
        'contest_problem__contest', # Filter by the contest name
        'contest_problem__problem', # Filter by the specific problem name
        'participant', # Filter by the participant
    )
    search_fields = (
        'participant__username', # Search by participant's username
        'contest_problem__contest__name', # Search by contest name
        'contest_problem__problem__name', # Search by problem name
        'code', # Search within submitted code
    )
    date_hierarchy = 'submitted_at'
    ordering = ('-submitted_at',) # Most recent submissions first
    raw_id_fields = ('participant', 'contest_problem') # Use raw ID fields for ForeignKeys

    # Add a custom method to display the related problem's name
    def contest_problem(self, obj):
        return f"{obj.contest_problem.contest.name} - {obj.contest_problem.problem.name}"
    contest_problem.short_description = "Contest Problem"