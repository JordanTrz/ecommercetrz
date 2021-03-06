from django import forms
from django.forms import ModelForm

from django.contrib.auth.models import User

class ClienteForm(forms.Form):
  nombre = forms.CharField(label="Nombre",max_length=200,required=True)
  apellidos = forms.CharField(label="Apellidos",max_length=200,required=True)
  email = forms.EmailField(required=True)
  direccion = forms.CharField(widget=forms.Textarea,required=True)
  telefono = forms.CharField(max_length=20)
  usuario = forms.CharField(max_length=20,required=True)
  password = forms.CharField(widget=forms.PasswordInput)

# class UserForm(ModelForm):
#   class Meta:
#     model = User
#     fields = ['first_name','last_name', 'username', 'email', 'password']