from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import auth_login
from django.db.models import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .forms import PhonenumberForm, RegisterForm
from .models import UbaarUser

# Create your views here.


def check_user_phonenumber(request):
    """
    Handle loging in with phonenumber
    """
    if request.method == "POST":
        form = PhonenumberForm(request.POST)
        if form.is_valid():
            # check if the user exists
            try:
                user = UbaarUser.objects.get(phonenumber=form.data["phonenumber"])
                # if exists, redirect a view that handles login
                return HttpResponseRedirect(reverse("users:login"))
            except ObjectDoesNotExist:
                # if doesn't exist
                # redirect to a register view
                return render(request, "users/register.html", {"form": RegisterForm})
    else:
        # first of all, show the phonenumber form to get the user's phonenumber
        return render(request, "users/phonenumber.html", {"form": PhonenumberForm})


def login(request):
    if request.method == "POST":
        # if user is posting to this view
        form = AuthenticationForm(request.POST)
        if form.is_valid():
            # if form is valid (here it means password constraints)
            auth_login(request, form.get_user())
            return HttpResponseRedirect(request, "users/success.html")
        else:
            # if form was not valid (bad password probably)
            return render(
                request, "users/login.html", {"form": form, "errors": "some error"}
            )
    # if user redirected to this view from check_user_phonenumber view
    return render(request, "users/login.html", {"form": form})
