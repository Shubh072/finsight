import re

EMAIL_REGEX = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'


def validate_email(email):
    return re.match(EMAIL_REGEX, email) is not None


def validate_password(password):
    return re.match(PASSWORD_REGEX, password) is not None


def validate_phone(phone):
    return phone.isdigit() and len(phone) >= 8