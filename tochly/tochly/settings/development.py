from .base import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': config('TOCHLY_DB'),
        'USER': config('TOCHLY_USER'),
        'PASSWORD': config('TOCHLY_PASSWORD'),
        'HOST': 'localhost'
    }
}

