from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
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
    
    def __str__(self):
        return self.username


    # bio = models.TextField(blank=True, null=True)
    # profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)