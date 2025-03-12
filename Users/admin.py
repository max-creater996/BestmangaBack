from django.contrib import admin
from .models import User

@admin.register(User)
class Admin(admin.ModelAdmin):
    model = User
    list_display = ('username', 'email', 'first_name', 'last_name')
