"""Development sozlamalari."""
from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += ["django_extensions"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
