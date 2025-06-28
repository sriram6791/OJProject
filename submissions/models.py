# submissions/models.py

from django.db import models
from users.models import CustomUser # Import CustomUser from users app
from problems.models import Problem # Import Problem from problems app

class Submission(models.Model):
    """
    Represents a user's code submission to a problem.
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='submissions',
        help_text="The user who made this submission."
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='submissions',
        help_text="The problem this submission is for."
    )
    code = models.TextField(help_text="The submitted code.")
    language = models.CharField(max_length=50, help_text="Programming language used (e.g., 'python', 'cpp', 'java').")

    # Fields for detailed verdict and status, as per HLD update
    status_choices = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('finished', 'Finished'),
    )
    status = models.CharField(
        max_length=20,
        choices=status_choices,
        default='pending',
        help_text="Current status of the submission evaluation."
    )

    final_verdict_choices = (
        ('accepted', 'Accepted'),
        ('wrong_answer', 'Wrong Answer'),
        ('time_limit_exceeded', 'Time Limit Exceeded'),
        ('memory_limit_exceeded', 'Memory Limit Exceeded'),
        ('runtime_error', 'Runtime Error'),
        ('compilation_error', 'Compilation Error'),
        ('pending', 'Pending Evaluation'), # Should match status_choices 'pending'
    )
    final_verdict = models.CharField(
        max_length=50,
        choices=final_verdict_choices,
        default='pending',
        help_text="Final verdict of the submission."
    )
    passed_test_cases = models.IntegerField(
        default=0,
        blank=True,
        null=True,
        help_text="Number of test cases passed."
    )
    total_test_cases = models.IntegerField(
        default=0,
        blank=True,
        null=True,
        help_text="Total number of test cases for the problem."
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if compilation or runtime error occurred."
    )

    submitted_at = models.DateTimeField(auto_now_add=True)
    execution_time = models.FloatField(
        blank=True,
        null=True,
        help_text="Execution time in seconds."
    )
    memory_used = models.FloatField(
        blank=True,
        null=True,
        help_text="Memory used in KB or MB."
    )

    class Meta:
        verbose_name = "Submission"
        verbose_name_plural = "Submissions"
        ordering = ['-submitted_at'] # Order by most recent submission

    def __str__(self):
        return f"{self.user.username}'s submission for {self.problem.name} ({self.final_verdict})"