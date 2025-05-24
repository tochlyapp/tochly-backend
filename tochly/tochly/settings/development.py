import os
from dotenv import load_dotenv
from .base import *


DEBUG = True

# load env config
load_dotenv(dotenv_path=BASE_DIR / '../.env.dev')


ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'host.docker.internal']

# celery
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
CELERY_TASK_SERIALIZER = 'json'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': getenv('DB_NAME'),
        'USER': getenv('DB_USER'),
        'PASSWORD': getenv('DB_PASSWORD'),
        'HOST': 'db',
        'PORT': 5432,
    }
}
