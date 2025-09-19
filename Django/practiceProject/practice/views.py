from django.shortcuts import render
from .models import PracticeVarity, School
from django.shortcuts import get_object_or_404
from .forms import PracticeVarityForm

def practice(request):
  practice = PracticeVarity.objects.all()
  return render(request, 'practice/practice.html', {'practice':practice})

def practice_detail(request, practice_id):
  practice = get_object_or_404(PracticeVarity, pk=practice_id)
  return render(request, 'practice/practice_detail.html', {"practice":practice})

def school_view(request):
  schools = None
  if request.method == 'POST':
    form = PracticeVarityForm(request.POST)
    if form.is_valid():
      practice_varity = form.cleaned_data['practice_varity']
      schools = School.objects.filter(practice_varieties=practice_varity)
  else: 
    form = PracticeVarityForm()
  return render(request, 'practice/school.html', {'schools': schools, "form":form})

def order(request):
  return render(request, 'practice/order.html')
