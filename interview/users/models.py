from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.


class UbaarUser(AbstractUser):
    phonenumber = models.CharField(
        unique=True,
        # TODO:
        # validator = [phonenumber_validator],
        max_length=12,
    )

    def __str__(self):
        return f"{self.phonenumber}"


class UbaarUserProfile(models.Model):
    user = models.OneToOneField(to=UbaarUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


@receiver(post_save, sender=UbaarUser)
def create_ubaaruser_profile(sender, instance, created, **kawrgs):
    if created:
        UbaarUserProfile.objects.create(user=instance)
