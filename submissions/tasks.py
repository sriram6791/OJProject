# submissions/tasks.py

from celery import shared_task
import time # For simulation, remove in production
from judge_core.judge import evaluate_solution, evaluate_contest_solution # Import the core judge function

@shared_task(bind=True)
def evaluate_submission_task(self, submission_id):
    """
    Celery task to evaluate a user's code submission.
    """
    print(f"Starting evaluation for submission ID: {submission_id}")
    try:
        # Call the core judge logic
        evaluate_solution(submission_id)
        print(f"Finished evaluation for submission ID: {submission_id}")
    except Exception as e:
        print(f"Task failed for submission ID: {submission_id} with error: {e}")
        # In a real system, you'd want more robust error logging here
        # and possibly update the submission status to 'error'
    
@shared_task(bind=True)
def evaluate_contest_submission_task(self, contest_submission_id):
    """
    Celery task to evaluate a user's code submission for contest problems.
    """
    print(f"Starting evaluation for contest submission ID: {contest_submission_id}")
    try:
        # Call the core judge logic for contest submissions
        evaluate_contest_solution(contest_submission_id)
        print(f"Finished evaluation for contest submission ID: {contest_submission_id}")
    except Exception as e:
        print(f"Task failed for contest submission ID: {contest_submission_id} with error: {e}")
        # In a real system, you'd want more robust error logging here
        # and possibly update the submission status to 'error'