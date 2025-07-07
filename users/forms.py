from django import forms
from django.contrib.auth.forms import UserCreationForm , AuthenticationForm
from django.contrib.auth import authenticate
from .models import CustomUser


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True,help_text='Required. Enter a vaild email address.')
    first_row = forms.CharField(max_length=30,required=False)
    last_row = forms.CharField(max_length=150,required=False)
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES,initial='student',required=True)
    
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('email' , 'first_name' , 'last_name' , 'role',)
        
    def clean_email(self):
            email = self.cleaned_data.get('email')
            if CustomUser.objects.filter(email= email).exists():
                raise forms.ValidationError( " Auser with that email alredy exists.")
            return email
        
class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username or Email")
    password = forms.CharField(widget=forms.PasswordInput)
    
    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        
        if username and password:
            self.user_cache = authenticate(self.request,username = username,password = password)
            
            if self.user_cache is None:
                try:
                    user_by_email = CustomUser.objects.get(email = username)
                    self.user_cache = authenticate(self.request,username=user_by_email.username,password=password)
                except CustomUser.DoesNotExist:
                    pass
            
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code = 'invalid_login',
                    params= {'username':self.username_field.verbose_name},
                )
        return self.cleaned_data