from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (AuthenticationForm,
                                       BaseUserCreationForm, UserCreationForm)
from django.core.validators import MinLengthValidator
from django.forms import CharField, Form, ModelForm, SlugField, TextInput

from .validators import phonenumber_validator

user = get_user_model()

phonenumber_field = CharField(
    label="phonenumber",
    max_length=12,
    validators=[phonenumber_validator],
    widget=TextInput(attrs={"type": "tel"}),
)


class PhonenumberForm(Form):
    phonenumber = phonenumber_field


class RegisterForm(UserCreationForm):
    username = phonenumber_field

    class Meta:
        model = user
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )


class LoginForm(AuthenticationForm):
    username = phonenumber_field

    class Meta:
        model = user
        fields = ("username", "password")


class OTPForm(Form):
    # TODO: make a widget
    otp = CharField(
        label="otp", max_length=6, validators=[MinLengthValidator(limit_value=6)]
    )
    otp_cache_key = SlugField(label="otp_cache_key", max_length=20)


class RegisterInfoForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["email"].required = True

    class Meta:
        model = user
        fields = ("first_name", "last_name", "email")


class RegisterPasswordForm(BaseUserCreationForm):
    password2 = None

    class Meta:
        model = user
        fields = ("password1",)
