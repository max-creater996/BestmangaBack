from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now

class User(AbstractUser):
    gender=(
        ("мужчина","мужчина"),
        ("женщина","женщина"),
    )
    gender_choices = models.CharField(max_length=69,choices=gender,null=True)
    avatar_img = models.ImageField(upload_to="photos/%Y/%m/%d/",null=True)
    background_img = models.ImageField(upload_to="photos/%Y/%m/%d/",null=True)
    background_img_front = models.IntegerField(null=True)
    img_frame = models.IntegerField(null=True)
    bookmarks = models.ManyToManyField("Manga.Manga", blank=True, related_name="bookmarks")
    last_join = models.DateTimeField(auto_now_add=True,null=True,auto_created=True)
    is_writer = models.BooleanField(default=False,null=True)
    phone = models.CharField(max_length=10,null=True)
    last_seen = models.DateTimeField(default=now)

    def update_last_seen(self):
        self.last_seen = now()
        self.save(update_fields=['last_seen'])

    def __str__(self):
        return self.username