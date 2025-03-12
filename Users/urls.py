from .views import *
from django.urls import path
urlpatterns = [
    path('me', UserProfileView.as_view(),name="user_account"),
    path("<int:pk>", User_profile.as_view()),
]

