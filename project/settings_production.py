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

SENDGRID_API_KEY = os.environ['SENDGRID_API_KEY']

ALLOWED_HOSTS = ['gifterator3000.herokuapp.com', 'herokuapp.com', 'gifterator3k.com', 'www.gifterator3k.com']

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

SEND_EMAILS = True
