from rest_framework import serializers
from .models import Tweet, User

class TweetSerializer(serializers.ModelSerializer):
  class Meta:
    model = Tweet
    fields = ['id', 'user', 'text']