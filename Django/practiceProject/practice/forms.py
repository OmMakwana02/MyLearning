from django import forms 
from .models import PracticeVarity

class PracticeVarityForm(forms.Form):
  practice_varity = forms.ModelChoiceField\
    (queryset=PracticeVarity.objects.all(), label="Select Practice Varity")