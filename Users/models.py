from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    gender=(
        ("мужчина","мужчина"),
        ("женщина","женщина"),
    )
    gender_choices=models.CharField(max_length=69,choices=gender,null=True)
    avatar_img = models.ImageField(upload_to="photos/%Y/%m/%d/")
    last_join = models.DateTimeField(auto_now_add=True,null=True,auto_created=True)
    is_writer = models.BooleanField(default=False,null=True)
    phone = models.CharField(max_length=10,null=True)

    def __str__(self):
        return self.username