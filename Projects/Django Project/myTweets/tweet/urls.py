
from django.urls import path
from django.conf import settings
from . import views

from rest_framework.urlpatterns import format_suffix_patterns


urlpatterns = [
    path("", views.tweet_list, name = "tweet_list"),

    path("create/", views.tweet_create, name = "tweet_create"),
    
    path("<int:tweet_id>/edit/", views.tweet_edit, name = "tweet_edit"),
    
    path("<int:tweet_id>/delete/", views.tweet_delete, name = "tweet_delete"),
    
    path("register/", views.register, name= "register"),
    
    path("users/", views.users, name="users"),  # Fixed: removed user_id parameter
    
    path("users/<str:username>/", views.user_tweets, name="user_tweets"),  # Fixed: changed to username and proper pattern

    path("tjson/", views.tweets_json, name = "json"),
    path("tjson/<int:id>", views.tweet_detail, name = "tweet_detail"),
]

urlpatterns = format_suffix_patterns(urlpatterns)