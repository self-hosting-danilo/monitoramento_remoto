from django.contrib.auth.models import AbstractUser
from django.db import models
from dashboard.models import Hospital

class CustomUser(AbstractUser):
    hospital = models.ForeignKey(
        Hospital, on_delete=models.SET_NULL, null=True, blank=True
    )
