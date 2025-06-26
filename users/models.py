from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class CustomUser(AbstractUser):
    """
    # Django AbstractUser class already has 
        - username
        - first_name
        - last_name
        - email
        - is_Staff 
        - is_active
        - date_joined
    """ 
    
    ROLE_CHOICES = (
        ('student' , 'Student'),
        ('problem_setter' , 'Problem Setter'),
        ('admin' , 'Admin')
    )
    
    role = models.CharField(max_length=20,choices=ROLE_CHOICES,default='student')

    # bio = models.TextField(blank=True, null=True)
    # profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    