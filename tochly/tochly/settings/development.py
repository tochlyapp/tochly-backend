from .base import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost']


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('TOCHLY_DB'),
        'USER': config('TOCHLY_USER'),
        'PASSWORD': config('TOCHLY_PASSWORD'),
        'HOST':config('HOST')
    }
}

