import phonenumbers
from django.core.exceptions import ValidationError


def phonenumber_validator(pn):
    phonenumber = phonenumbers.parse(pn, "IR")
    if not phonenumbers.is_valid_number(phonenumber):
        raise ValidationError(f"{pn} is not a valid phonenumber", params={"value": pn})
