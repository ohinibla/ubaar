from random import randint
from secrets import token_urlsafe

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import get_user_model
from django.core.cache import cache
from django.db.models import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import render, reverse

from .forms import (LoginForm, OTPForm, PhonenumberForm, RegisterForm,
                    RegisterInfoForm, RegisterPasswordForm)
from .otp import OTP

# Create your views here.

auth_user = get_user_model()


def check_user_phonenumber(request):
    """
    Handle logging in with phonenumber
    """
    if request.method == "POST":
        form = PhonenumberForm(request.POST)
        if form.is_valid():
            phonenumber = form.cleaned_data.get("phonenumber")
            # check if the user exists
            try:
                user = auth_user.objects.get(username=phonenumber)
                # if exists, redirect a view that handles login
                # get user's password
                return render(
                    request,
                    "users/login.html",
                    {"form": LoginForm(initial={"username": phonenumber})},
                )
            except ObjectDoesNotExist:
                # if doesn't exist
                # redirect to a register view with the phonenumber and the corresponding cache key
                return HttpResponseRedirect(
                    reverse("users:register", args=[phonenumber])
                )
        # if phonenumber is not valid
        return render(
            request,
            "users/phonenumber.html",
            {
                "form": PhonenumberForm(initial=form.data),
                "errors": form.errors,
            },
        )
    else:
        # first of all, show the phonenumber form to get the user's phonenumber
        return render(request, "users/phonenumber.html", {"form": PhonenumberForm})


def login_user(request):
    """
    Handle login
    """
    if request.method == "POST":
        print(request.POST)
        # user is posting to this view
        form = LoginForm(data=request.POST)
        # first validate the form
        if form.is_valid():
            # then authenticate the user
            user = authenticate(
                username=form.cleaned_data.get("username"),
                password=form.cleaned_data.get("password"),
            )
            if user:
                # if authenticated, login
                login(request, form.get_user())
                return render(request, "users/success.html")
            else:
                # if not authenticated, return to login
                return render(
                    request, "users/login.html", {"form": form, "errors": form.errors}
                )
        else:
            # if data is not right, return to login with errors
            return render(
                request, "users/login.html", {"form": form, "errors": form.errors}
            )
    # if user redirected to this view from check_user_phonenumber view since the user exists
    return render(request, "users/login.html", {"form": LoginForm})


def register_otp(request, phonenumber):
    """
    Handle registration
    """
    # user has been redirected to get registered
    if request.method == "GET":
        # initiate an otp process
        # create a random 6 digit string
        random_otp = OTP.generate_random_otp()
        print(f"🔴🟢   {random_otp = }")
        # store the otp in cache
        # generate a url_safe token as cache key, reason being it can be sent back as post and cannot be guessed
        otp_cache_key = token_urlsafe(20)[:20]
        # save it in cache
        cache.set(otp_cache_key, random_otp)
        return render(
            request,
            "users/register.html",
            {"form": OTPForm(initial={"otp_cache_key": otp_cache_key})},
        )
    if request.method == "POST":
        # user is registering with opt value and an implicit otp_cache_key
        # populate the otp form
        form = OTPForm(request.POST)
        if form.is_valid():
            # if otp and cache_key validations pass
            # check whether otp value is correct
            # get user's otp value
            user_otp_value = form.cleaned_data.get("otp")
            # retrieve otp value from cache
            otp_cache_key = form.cleaned_data.get("otp_cache_key")
            server_otp_value = cache.get(otp_cache_key)
            if user_otp_value == server_otp_value:
                # proceed with registration process
                # pass phonenumber as session, so that the user can be created with all
                # the gathered info in subsequent views at the last step
                request.session["username"] = phonenumber
                return HttpResponseRedirect(reverse("users:register_info"))
            else:
                return render(
                    request,
                    "users/register.html",
                    {
                        "form": OTPForm(initial={"otp_cache_key": otp_cache_key}),
                        "errors": "otp doesn't match",
                    },
                )

        # if form validation doesn't pass
        return render(
            request,
            "users/register.html",
            {
                "form": OTPForm(
                    initial={"otp_cache_key": form.cleaned_data.get("otp_cache_key")}
                ),
                "errors": form.errors,
            },
        )


def register_info(request):
    if request.method == "POST":
        form = RegisterInfoForm(request.POST)
        if form.is_valid():
            # if user entered correct format of the data, proceed to password form
            # update session first
            request.session["first_name"] = form.cleaned_data.get("first_name")
            request.session["last_name"] = form.cleaned_data.get("last_name")
            request.session["email"] = form.cleaned_data.get("email")
            return HttpResponseRedirect(reverse("users:register_password"))

    # if user is redirected here
    # check whether user is redirected with a phonenumber
    if request.session.get("username"):
        # render info entry form
        return render(request, "users/register_info.html", {"form": RegisterInfoForm})
    # if not redirected with a phonenumber
    else:
        # return to home
        return HttpResponseRedirect(reverse("users:check_user_phonenumber"))


def register_password(request):
    # get all the user data from cache
    user_data = {
        "first_name": request.session.get("first_name"),
        "last_name": request.session.get("last_name"),
        "email": request.session.get("email"),
        "username": request.session.get("username"),
    }
    # if user is redirected here
    if request.method == "GET":
        # if user have completed previous steps (user data exists)
        if all(user_data.values()):
            # get user's password
            return render(
                request, "users/register_password.html", {"form": RegisterPasswordForm}
            )
        # if user data is not complete
        return HttpResponseRedirect(reverse("users:check"))
    if request.method == "POST":
        # update user_data dictionary with password from form
        user_data["password1"] = request.POST.get("password1")
        user_data["password2"] = user_data["password1"]
        # populate `registration form` with all the user data
        # using RegisterForm since all the data is gathered now
        form = RegisterForm(user_data)
        if form.is_valid():
            # if data is valid, create a user object
            # user, created = auth_user.objects.create(form)
            user = form.save()
            login(request, user)
            return render(request, "users/success.html")
        # if data were not valid (since we are instantiating RegisterForm with all the user data
        # redirect to register_info)
        return render(
            request,
            "users/register_info.html",
            {"form": RegisterInfoForm, "errors": form.errors},
        )


# NOTE: can i authenticate without user and pass, i mean a temporary authentication with otp
# FIX: check urls
