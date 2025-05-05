from django.contrib.auth.models import User
from django.db import models

# from django.db.models.signals import post_save
# from django.dispatch import receiver

# Create your models here.


class UbaarUserProfile(models.Model):
    user = models.OneToOneField(to=User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# @receiver(post_save, sender=User)
# def create_ubaaruser_profile(sender, instance, created, **kawrgs):
#     if created:
#         UbaarUserProfile.objects.create(user=instance)
