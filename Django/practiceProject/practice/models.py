from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.
class PracticeVarity(models.Model):
  PRACTICE_TYPE_CHOICE = [
    ('RD', 'READING'),
    ('WR', 'WRITING'),
    ('LR', 'LEARNING'),
    ('SL', 'SOLVING'),
    ('RB', 'REMEMBERING'),
  ]
  name = models.CharField(max_length = 100)
  image = models.ImageField(upload_to='practice/')
  date_added = models.DateTimeField(default=timezone.now)
  type = models.CharField(max_length=2,choices = PRACTICE_TYPE_CHOICE)
  description = models.TextField(default='')
  time_req = models.IntegerField(default=0)

  def __str__(self):
    return self.name
  
# One to Many
class PracticeReview(models.Model):
  practice = models.ForeignKey(PracticeVarity, on_delete=models.CASCADE, related_name='reviews') 
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  rating = models.IntegerField(default=0, choices=[(i,i) for i in range(1, 6)])
  comment = models.TextField()
  date_added = models.DateTimeField(default=timezone.now)

  def __str__(self):
    return f'{self.user.username} reviewed {self.practice.name} '
  

# Many to Many
class School(models.Model):
  name = models.CharField(max_length=100)
  location = models.CharField(max_length=100)
  practice_varieties = models.ManyToManyField(PracticeVarity, related_name='schools')

  def __str__(self):
    return self.name
  
# One to One
class Certificate(models.Model):
  practice = models.OneToOneField(PracticeVarity, on_delete=models.CASCADE, related_name='certificate')
  certificate_number = models.CharField(max_length=100) # make unique=true
  issued_date = models.DateTimeField(default=timezone.now)
  valid_until = models.DateTimeField()

  def __str__(self):
    return f'Certificate for {self.name.practice}'
