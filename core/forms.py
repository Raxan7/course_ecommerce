from django import forms
from django.contrib.auth.models import User


from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(max_length=255, required=True)  # Added username field
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(
        max_length=15,
        required=True,
        validators=[RegexValidator(r'^[0-9]+$', 'Enter a valid phone number.')]
    )
    country_code = forms.CharField(max_length=5, initial='+255')
    terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'}),
        error_messages={'required': 'You must accept the terms and conditions'}
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 
                 'country_code', 'phone', 'password1', 'password2', 'terms')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add similar widget attrs for other fields if needed


class CheckoutForm(forms.Form):
    stripe_token = forms.CharField(max_length=255)  # Replace with Pesapal-specific fields if needed

class LoginForm(forms.Form):
    username = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'placeholder': 'Username'}))  # Updated max_length
    password = forms.CharField(max_length=128, required=True, widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
