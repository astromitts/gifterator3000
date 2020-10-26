import os
from project.settings import *  # noqa

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['DATABASE_NAME'],
        'USER': os.environ['DATABASE_USER'],
        'PASSWORD': os.environ['DATABASE_PASSWORD'],
        'HOST': os.environ['DATABASE_HOST'],
        'PORT': '5432'
    }
}

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = os.environ['GMAIL_USER']
EMAIL_HOST_PASSWORD = os.environ['GMAIL_PASS']
EMAIL_PORT = 587
EMAIL_USE_TLS = True

SENDGRID_API_KEY = os.environ['SENDGRID_API_KEY']

ALLOWED_HOSTS = ['gifterator3000.herokuapp.com', 'herokuapp.com', ]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
