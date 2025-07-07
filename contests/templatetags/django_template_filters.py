from django import template
from contests.models import ContestSubmission # Import your ContestSubmission model

register = template.Library()

@register.filter
def first_submission_for_problem(submissions, problem):
    """
    Returns the first (latest) submission for a given problem from a queryset of submissions.
    Assumes the submissions queryset is already filtered by user and contest, and ordered by submitted_at DESC.
    """
    for submission in submissions:
        if submission.contest_problem.problem == problem:
            return submission
    return None