from datetime import datetime
from secrets import token_urlsafe

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import get_user_model
from django.core.cache import cache
from django.db.models import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import render, reverse

from .forms import (LoginForm, OTPForm, PhonenumberForm, RegisterForm,
                    RegisterInfoForm, RegisterPasswordForm)
from .otp import generate_random_otp
from .utils import ban_user_if_necessary, get_ban_remaining_time

# Create your views here.

auth_user = get_user_model()


def check_phonenumber(request):
    """
    Handle logging in with phonenumber
    """
    # check if the user is already banned or not
    if request.method == "POST":
        form = PhonenumberForm(request.POST)
        if form.is_valid():
            phonenumber = form.cleaned_data.get("phonenumber")
            # check if the user exists
            try:
                user = auth_user.objects.get(username=phonenumber)
                # set username in session
                request.session["username"] = phonenumber
                # if exists, redirect a view that handles login
                # get user's password
                return render(
                    request,
                    "users/login.html",
                    {"form": LoginForm(initial={"username": phonenumber})},
                )
            # if user obj doesn't exist
            except ObjectDoesNotExist:
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
    # first of all, show the phonenumber form to get the user's phonenumber
    return render(request, "users/phonenumber.html", {"form": PhonenumberForm})


def logout_user(request):
    """
    Logout user
    """
    if request.method == "POST":
        logout(request)
        return HttpResponseRedirect(reverse("users:check"))
    return HttpResponseRedirect(reverse("users:check"))


def login_user(request):
    """
    Handle login
    """
    username = request.session.get("phonenumber")
    user_ip_address = request.META["REMOTE_ADDR"]
    # set ban time remaining to be the greater of banned by ip or banned by username
    # this way, ban period is insured to be at least BAN_PERIOD_MINUTE
    ban_remaining_time = max(
        get_ban_remaining_time(username), get_ban_remaining_time(user_ip_address)
    )
    is_user_banned = bool(ban_remaining_time)
    if request.method == "POST":
        # first check whether the user is banned or not
        username = request.POST.get("username")
        if not is_user_banned:
            # user is posting to this view
            form = LoginForm(data=request.POST)
            if form.is_valid():
                # then authenticate the user
                user = authenticate(
                    username=form.cleaned_data.get("username"),
                    password=form.cleaned_data.get("password"),
                )
                if user:
                    # if authenticated, login
                    login(request, form.get_user())
                    # clear the cache used in login attempts
                    cache.delete(username)
                    return render(request, "users/success.html")
                else:
                    return render(
                        request,
                        "users/login.html",
                        {"form": form, "errors": "user not logged in"},
                    )
            else:
                ctx = {"form": form, "errors": form.errors}
                is_user_banned = ban_user_if_necessary(
                    username
                ) and ban_user_if_necessary(user_ip_address)
                ban_remaining_time = max(
                    get_ban_remaining_time(username),
                    get_ban_remaining_time(user_ip_address),
                )
                if is_user_banned:
                    ctx["ban_error"] = f"user is banned for {ban_remaining_time}"

                return render(request, "users/login.html", ctx)
        else:
            # if user is already banned
            return render(
                request,
                "users/login.html",
                {
                    "form": LoginForm,
                    "ban_error": f"user is banned for {ban_remaining_time} minutes",
                },
            )
    # if user redirected to this view from another view since the user exists
    # check whether the user is banned or not
    if is_user_banned:
        return render(
            request,
            "users/login.html",
            {
                "form": LoginForm,
                "ban_error": f"user is banned for {ban_remaining_time}",
            },
        )

    # if user was not banned, on a get request, just render the form
    return render(request, "users/login.html", {"form": LoginForm})


def register_otp(request, phonenumber):
    """
    Handle registration
    """
    ban_remaining_time = get_ban_remaining_time(phonenumber)
    is_user_banned = bool(ban_remaining_time)
    # user has been redirected to get registered
    if request.method == "GET":
        # first check whether the user is banned
        # if banned don't proceed and return with an error
        if is_user_banned:
            # redirect to the check_user_phonenumber view
            return HttpResponseRedirect(reverse("users:check"))
        # initiate an otp process
        # create a random 6 digit string
        random_otp = generate_random_otp()
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
        # check whether the user is already banned or not (same as GET)
        # but redirect to check_user_phonenumber view instead
        if is_user_banned:
            return HttpResponseRedirect(reverse("users:check"))
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
                # clear the cache used in otp attempts
                cache.delete(phonenumber)
                # pass phonenumber as session, so that the user can be created with all
                # the gathered info in subsequent views at the last step
                request.session["username"] = phonenumber
                return HttpResponseRedirect(reverse("users:register_info"))
            else:
                # the same as login, but already use url arg (phonenumber) as identifier instead of session
                ctx = {"form": form, "errors": form.errors}
                ctx = {
                    "form": OTPForm(initial={"otp_cache_key": otp_cache_key}),
                    "form_errors": form.errors,
                    "otp_error": "otp doesn't match",
                }
                is_user_banned = ban_user_if_necessary(phonenumber)
                if is_user_banned:
                    ctx["ban_error"] = f"user is banned for {ban_remaining_time}"

                return render(request, "users/register.html", ctx)

        # if otp form validation doesn't pass
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
    """
    Register user info, first name, last name and email
    """
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
    """
    Register user password and finally create a user object
    """
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
