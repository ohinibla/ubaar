from django.contrib.auth.forms import UserCreationForm
from django.forms import CharField, Form, ModelForm, TextInput

from .models import UbaarUser


class PhonenumberForm(Form):
    phonenumber = CharField(
        validators=[], max_length=12, widget=TextInput(attrs={"type": "tel"})
    )


class RegisterForm(UserCreationForm):
    class Meta:

        # NOTE: should i use get_auth_model?
        model = UbaarUser
        fields = UserCreationForm.Meta.fields + ("phonenumber",)
