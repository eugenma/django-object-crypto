import getpass
import os
import sys


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Make sure the copy of pgcrypto in the directory above this one is used.
sys.path.insert(0, BASE_DIR)

SECRET_KEY = 'django_pgcrypto_tests__this_is_not_very_secret'

INSTALLED_APPS = [
    # TODO: This is required for pgcrypto
    'django.contrib.contenttypes',
    'pgcrypto',
    'core',
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },

   'postgres': {
       'ENGINE': 'django.db.backends.postgresql',
       'NAME': os.environ.get('PGCRYPTO_TEST_DATABASE', 'postgres'),
       'USER': os.environ.get('PGCRYPTO_TEST_USER', 'postgres'),
       'PASSWORD': os.environ.get('PGCRYPTO_TEST_PASSWORD', ''),
       'HOST': os.environ.get('PGCRYPTO_TEST_HOST', 'localhost'),
       'PORT': os.environ.get('PGCRYPTO_TEST_PORT', 5432),
   },
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

########
# PGCrypto Extensions
########
PGCRYPTO = {
    'USER_PROFILE': {
        'model': 'userprofile.UserProfile',
        'superkey_field': 'superkey',
        'user_field': 'user',
    },
    'VALID_CIPHERS': ('AES', 'Blowfish'),
    'CHECK_ARMOR': True,
    'CIPHER': 'Blowfish',
    'VERSIONED': False,
}

