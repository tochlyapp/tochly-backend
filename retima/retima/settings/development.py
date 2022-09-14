from .base import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': config('RETIMA_DB'),
        'USER': config('RETIMA_USER'),
        'PASSWORD': config('RETIMA_PASSWORD'),
        'HOST': 'localhost'
    }
}

