from django import template
from contests.models import ContestSubmission # Import your ContestSubmission model

register = template.Library()

@register.filter
def first_submission_for_problem(submissions, problem):
    """
    Returns the first (latest) submission for a given problem from a queryset of submissions.
    Assumes the submissions queryset is already filtered by user and contest.
    """
    if not submissions or not problem:
        return None
    
    # Filter the submissions for the specific problem and return the most recent one
    matching_submissions = [s for s in submissions if s.contest_problem.problem == problem]
    return matching_submissions[0] if matching_submissions else None