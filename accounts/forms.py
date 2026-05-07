from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
        'placeholder': 'you@example.com',
    }))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
        'placeholder': 'First name',
    }))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
        'placeholder': 'Last name',
    }))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Choose a username',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '••••••••',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full border-gray-200 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '••••••••',
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
        return user
