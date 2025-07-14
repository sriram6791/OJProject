from django.db import models

# Create your models here.
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from problems.models import Problem

class Contest(models.Model):
    name = models.CharField(max_length=255,unique=True,help_text="Name of the contest")
    description = models.TextField(help_text="Detailed description of the contest")
    start_time = models.DateTimeField(help_text="The official start time of the contest")
    end_time = models.DateTimeField(help_text="The official end time of the contest")
    
    STATUS_CHOICES = (
        ('upcoming','Upcoming'),
        ('active','Active'),
        ('ended','Ended'),
        ('cancelled','Cancelled')
    )
    
    # Status calculated based on start and end times manually
    status = models.CharField(max_length=10,choices=STATUS_CHOICES,default="upcoming",help_text="Current status of the contest")
    
    # Link to the user who created this contest
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_contests',
        help_text="User who created this contest"
    ) 
    
    # Many-to-many relationship with Problem through ContestProblem
    problems = models.ManyToManyField(
        Problem,
        through='ContestProblem',
        related_name='contests',
        help_text="Problems included in this contest"
    )
    
    # ManyToMany relationship with CustomUser for participants
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='contests_participated',
        blank=True,
        help_text= "Users who have registered or participated in this contest"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Contest'
        verbose_name_plural = 'Contests'
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['status']),  # Add an index on the status field
        ]
        
    def __str__(self):
        return self.name

    def get_duration(self):
        """Calculate the duration of the contest"""
        
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        
        return timedelta(0)
    
    def is_active(self):
        """Checks if the contest is currently active"""
        now = timezone.now()
        return self.start_time <= now <= self.end_time
    
    def is_upcoming(self):
        """Checks if the contest is upcoming"""
        now = timezone.now()
        return now <self.start_time
    
    def is_ended(self):
        """Checks if the contest is ended"""
        now = timezone.now()
        return now > self.end_time
    
    def is_registration_open(self):
        """Checks if registration for the contest is open"""
        # Registration is open for upcoming and active contests
        return self.status in ['upcoming', 'active']
    
    def update_status(self):
        """Updates the status field based on the current time"""
        if self.is_active():
            self.status = 'active'
        elif self.is_upcoming():
            self.status = 'upcoming'
        elif self.is_ended():
            self.status = 'ended'
        # 'cancelled' status is set manually, not automatically updated
        
    def save(self, *args, **kwargs):
        """Override save to update the status field"""
        self.update_status()
        super().save(*args, **kwargs)
    
    @classmethod
    def update_all_statuses(cls):
        """Updates the status of all contests based on their current time"""
        for contest in cls.objects.all():
            old_status = contest.status
            contest.update_status()
            if old_status != contest.status:
                contest.save()
    
class ContestProblem(models.Model):
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name='contest_problems',
        help_text="The contest this problem belongs to"
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='contest_instances',
        help_text="The problem itself"
    )
    points = models.IntegerField(
        default=100,
        help_text="Points awarded for solving this problem in this contest"
    )
    order_in_contest = models.IntegerField(
        help_text="The display order of the problem within the contest"
    )

    class Meta:
        verbose_name = "Contest Problem"
        verbose_name_plural = "Contest Problems"
        unique_together = ('contest', 'problem'), ('contest', 'order_in_contest')
        ordering = ['contest', 'order_in_contest']

    def __str__(self):
        return f"{self.contest.name} - Problem {self.order_in_contest}: {self.problem.name}"

class ContestSubmission(models.Model):
    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contest_submissions',
        help_text="The user who submitted the solution"
    )
    
    contest_problem = models.ForeignKey(
        ContestProblem,
        on_delete=models.CASCADE,
        related_name='submissions',
        help_text="The problem instance within a contest for which this submission was made"
    )
    
    submitted_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp of the submission")
    code = models.TextField(help_text="The submitted code")
    
    # Fields for detailed verdict and status, exactly like problems module
    # Consolidated status_choices to avoid re-definition
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
        ('pending', 'Pending Evaluation'), # This is the initial state for final_verdict
        ('judging_error', 'Judging Error'), # Ensure this is present
    )
    final_verdict = models.CharField(
        max_length=50,
        choices=final_verdict_choices,
        default='pending',
        help_text="Final verdict of the submission."
    )
    
    score = models.IntegerField(
        default=0,
        help_text="Score obtained for this submission"
    )
    
    test_cases_passed = models.IntegerField(default=0, help_text="Number of test cases passed")
    total_test_cases = models.IntegerField(default=0, help_text="Total number of test cases")
    language = models.CharField(max_length=50, default='python', help_text="Programming language used for the submission")
    judge_output = models.TextField(blank=True, null=True, help_text="Output/error messages from the judge")
    execution_time = models.FloatField(default=0.0, help_text="Execution time in seconds")
    memory_used = models.FloatField(default=0.0, help_text="Memory used in MB")

    class Meta:
        verbose_name = "Contest Submission"
        verbose_name_plural = "Contest Submissions"
        ordering = ['-submitted_at'] 

    def __str__(self):
        return f"Submission by {self.participant.username} for {self.contest_problem.problem.name} in {self.contest_problem.contest.name} ({self.final_verdict})"
        
    def clean(self):
        """Validate model fields before saving"""
        super().clean()
        # Ensure status is one of the valid choices
        valid_statuses = dict(self.status_choices).keys()
        if self.status not in valid_statuses:
            self.status = 'finished'  # Default to finished if invalid status
            
        # Ensure final_verdict is one of the valid choices
        valid_verdicts = dict(self.final_verdict_choices).keys()
        if self.final_verdict not in valid_verdicts:
            self.final_verdict = 'pending'  # Default to pending if invalid verdict
            
    def save(self, *args, **kwargs):
        """Override save to ensure clean is called"""
        self.clean()
        super().save(*args, **kwargs)

    def get_status_display(self):
        """Get the human-readable status"""
        try:
            return dict(self.status_choices)[self.status]
        except KeyError:
            self.status = 'finished'  # Fix invalid status
            self.save()
            return dict(self.status_choices)[self.status]
        
    def get_final_verdict_display(self):
        """Get the human-readable final verdict"""
        try:
            return dict(self.final_verdict_choices)[self.final_verdict]
        except KeyError:
            self.final_verdict = 'pending'  # Fix invalid verdict
            self.save()
            return dict(self.final_verdict_choices)[self.final_verdict]