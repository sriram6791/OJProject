from django.db import models
from users.models import CustomUser
# Create your models here.


class Problem(models.Model):
    name = models.CharField(max_length=255, unique=True,help_text="Name of the problem")
    statement = models.TextField(help_text="Full problem description")
    difficulty_choices = (
        ('easy','Easy'),
        ('medium' ,'Medium'),
        ('hard', 'Hard'),
    )
    
    difficulty = models.CharField(
        max_length=10,
        choices=difficulty_choices,
        default='easy',
        help_text="Difficulty level of the problem"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Linking problems to the creator , one creator can create many problems so this is a one to many kind of relation and for this we use Foreignkey
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_problems',
        help_text="User who created this problem"
    )
    
    class Meta:
        verbose_name = "Problems"
        verbose_name_plural = "Problems"
        ordering = ['name']
        
    def __str__(self):
        return self.name
    
    
class TestCase(models.Model):
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="test_cases",
        help_text="The problem this testcase belongs to."
    )
    
    input_data = models.TextField(help_text="Input for the test case.")
    expected_output = models.TextField(help_text="Expected output for the testcase")
    is_hidden = models.BooleanField(
        default=True,
        help_text="If True this test case is hidden from users."
    )
    
    order = models.IntegerField(default=0,help_text="Order of the test case.")
    
    class Meta:
        verbose_name = "Test Case"
        verbose_name_plural = "Test Cases"
        unique_together = ('problem', 'order') # Ensures unique ordering per problem
        ordering = ['order']

    def __str__(self):
        return f"Test Case {self.order} for {self.problem.name}"
    

class Submission(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='submission',
        help_text="The user who made this submission"
    )
    
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='submissions',
        help_text="The problem this submission is for."
    )
    
    code = models.TextField(help_text="The submission code.")
    language = models.CharField(max_length=50,help_text="Programming language used (e.g., 'Python', 'C++', 'Java').")
    
    status_choices = (
        ('pending','Pending'),
        ('processing','Processing'),
        ('finished','Finished'),
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