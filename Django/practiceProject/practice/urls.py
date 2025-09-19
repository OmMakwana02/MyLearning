from django.urls import path
from . import views


urlpatterns = [
    path('', views.practice, name='practice'), # We dont write the path for home page...its the default page.
    path('<int:practice_id>/', views.practice_detail, name='practice_detail'),
    path('school/', views.school_view, name='school'),
    path('order/', views.order, name='order')

]
