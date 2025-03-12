from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import User_serializers


class User_profile(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = User_serializers
    permission_classes = [IsAuthenticated,]

class UserProfileView(generics.RetrieveAPIView):
    serializer_class = User_serializers
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user