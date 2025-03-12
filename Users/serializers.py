from rest_framework import serializers

from .models import *

class User_serializers(serializers.ModelSerializer):
    bookmarks = serializers.StringRelatedField(read_only=True)
    class Meta:
        model=User
        fields="__all__"
