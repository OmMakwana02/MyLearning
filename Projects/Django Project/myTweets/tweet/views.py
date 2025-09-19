from django.shortcuts import render
from .models import Tweet
from .forms import TweetForm, UserRegisterForm
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User

from .serializers import TweetSerializer
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Create your views here.
def index(request):
  return render(request, 'tweet/index.html')

def tweet_list(request):
  tweets = Tweet.objects.all().order_by('-created_at')
  return render(request, "tweet_list.html", {"tweets": tweets})

@login_required
def tweet_create(request):
  if request.method == "POST":
    form = TweetForm(request.POST, request.FILES)
    if form.is_valid():
      tweet = form.save(commit=False)
      tweet.user = request.user
      tweet.save()
      return redirect("tweet_list")
  else:
    form = TweetForm()
  return render(request, "tweet_form.html", {"form":form})

@login_required
def tweet_edit(request, tweet_id):
  # tweet = get_object_or_404(model_name, pk, user=request.user)
  # this is bcoz the user that has logged in can only send the edit_tweet request.

  tweet = get_object_or_404(Tweet, pk=tweet_id, user=request.user)
  if request.method == "POST":
    form = TweetForm(request.POST, request.FILES, instance=tweet)  
    # instance is used to edit the existing tweet. We give this to know that we are editing the old tweet only. 
    if form.is_valid():
      tweet = form.save(commit=False)
      tweet.user = request.user
      tweet.save()
      return redirect("tweet_list")
  else:
    form = TweetForm(instance = tweet) # We add the instance to the form so that it can be edited.
  return render(request, "tweet_form.html", {"form":form})

@login_required
def tweet_delete(request, tweet_id):
  tweet = get_object_or_404(Tweet, pk=tweet_id, user=request.user)
  if request.method == "POST":
    tweet.delete()
    return redirect("tweet_list")
  return render(request, 'tweet_confirm_delete.html', {"tweet": tweet})

def register(request):
  if request.method == "POST":
    form = UserRegisterForm(request.POST)
    if form.is_valid():
      user = form.save(commit=False)
      user.set_password(form.cleaned_data['password1'])
      user.save()
      login(request, user)
      return redirect("tweet_list")
    # After registering the user, we log them in automatically and redirect to the tweet list.
  else:
    form = UserRegisterForm

  return render(request, 'registration/register.html', {"form": form})

def users(request):
  # Fixed: Get actual User objects instead of just usernames
  users = User.objects.filter(tweet__isnull=False).distinct()
  return render(request, 'users.html', {'users': users})

def user_tweets(request, username):
  tweets = Tweet.objects.filter(user__username=username).order_by('-created_at')
  if not tweets:
    return render(request, 'no_tweets.html', {'username': username})
  return render(request, 'user_tweets.html', {'tweets': tweets, 'username': username})

@api_view(['GET', 'POST'])
def tweets_json(request, fromat=None):

  if request.method == "GET":
    tweet = Tweet.objects.all()
    serializer = TweetSerializer(tweet, many=True)
    return JsonResponse({"tweets":serializer.data}, safe=False)
  
  if request.method == "POST":
    serializer = TweetSerializer(data=request.data)
    if serializer.is_valid():
      serializer.save()
      return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def tweet_detail(request, id, format=None):
  tweet = Tweet.objects.get(pk=id)

  if request.method == "GET":
    serializer = TweetSerializer(tweet)
    return Response(serializer.data)
  elif request.method == "PUT":
    serializer = TweetSerializer(tweet, data=request.data)
    if serializer.is_valid():
      serializer.save()
      return Response(serializer.data)
    return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
  elif request.method == "DELETE":
    tweet.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)