# Django settings for tolmach project.

import os, slugify
import raven

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = True

# Bystrofix to make uwsgi daemonize work properly
# http://itekblog.com/ascii-codec-cant-encode-characters-in-position/
import sys
try:
    reload(sys)  # Python 2.7
    sys.setdefaultencoding('utf-8')
except NameError:
    try:
        from importlib import reload  # Python 3.4+
        reload(sys)
    except ImportError:
        from imp import reload  # Python 3.0 - 3.3
        reload(sys)

ADMINS = (
    ('Dmitry Chumak', 'mega.venik@gmail.com'),
)
SPARKPOST_API_KEY = os.environ.get("SPARKPOST_API_KEY", "")
if SPARKPOST_API_KEY:
    EMAIL_BACKEND = 'sparkpost.django.email_backend.SparkPostEmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.environ.get('MYSQL_DATABASE', 'tolmach'),  # Or path to database file if using sqlite3.
        'USER': os.environ.get('MYSQL_USER', 'tolmach'),
        'PASSWORD': os.environ.get('MYSQL_PASSWORD', ''),
        'HOST': os.environ.get('MYSQL_HOST', '127.0.0.1'),
        'PORT': os.environ.get('MYSQL_PORT', '3306'),
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

ES_HOST = os.environ.get('ES_HOST', '127.0.0.1')
ES_PORT = int(os.environ.get('ES_PORT', 9200))
PORT = int(os.environ.get("PORT", 0))
DOMAIN = os.environ.get("DOMAIN", "tolma.ch")
# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [DOMAIN]
WS_HOST = ("wss" if PORT == 443 else "ws") + f"://{DOMAIN}"
SERVER_EMAIL = f'noreply@email.{DOMAIN}'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Moscow'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'ru'

LANGUAGES = (
    ('ru', 'Russian'),
    ('en', 'English'),
    ('zh', 'Chinese'),
)

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get("SECRET_KEY", "")

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            "/var/www/tolma.ch/templates",
        ],
        'OPTIONS': {
            'loaders': ['django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader',
                        'django.template.loaders.eggs.Loader',],
            'context_processors': ['django.contrib.auth.context_processors.auth',
                                    'social_django.context_processors.backends',
                                    'social_django.context_processors.login_redirect',
                                    'django.template.context_processors.request',
                                    'django.contrib.messages.context_processors.messages',
                                    'django.template.context_processors.i18n',
                                    'tolmach.context_processors.ya_metrika',
                                    'tolmach.context_processors.less_debug',
                                    'tolmach.context_processors.base_domain',
                                    'tolmach.context_processors.logo_special',]
        }
    },
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'tolmach.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'tolmach.wsgi.application'

INSTALLED_APPS = (
    'raven.contrib.django.raven_compat',
    #'south',
    'tolmach',
    'translations',
    'entries',
    'chat',
    'stats',
    'channels',
    'loginas',
    'social_auth_widget',
    'social_django',
    'simple_history',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'background_task',
    # 'ddtrace.contrib.django',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    # 'debug_toolbar',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'social_core.backends.twitter.TwitterOAuth',
    'social_core.backends.facebook.FacebookOAuth2',
    'social_core.backends.vk.VKOAuth2',
)

SOCIAL_AUTH_VK_OAUTH2_KEY = '***REMOVED***'
SOCIAL_AUTH_VK_OAUTH2_SECRET = '***REMOVED***'
SOCIAL_AUTH_VK_OAUTH2_EXTRA_DATA = [
    'photo_max'
]
SOCIAL_AUTH_TWITTER_KEY = '***REMOVED***'
SOCIAL_AUTH_TWITTER_SECRET = '***REMOVED***'

SOCIAL_AUTH_FACEBOOK_KEY = '***REMOVED***'
SOCIAL_AUTH_FACEBOOK_SECRET = '***REMOVED***'

LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/'
URL_PATH = ''

SOCIAL_AUTH_LOGIN_REDIRECT_URL = "/social-login/"

SOCIAL_AUTH_PROVIDERS = [
    {'id': p[0], 'name': p[1], 'icon': p[2]}
    for p in (
        ('vk-oauth2', u'Vk.com', 'vk'),
        ('facebook', u'Login via Facebook', 'facebook'),
        ('twitter', u'Twitter', 'twitter'),
    )
]

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.mail.mail_validation',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',

    'tolmach.pipeline.update_user_social_data',
)

RAVEN_CONFIG = {
    'dsn': '***REMOVED***',
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    'release': raven.fetch_git_sha(BASE_DIR),
    #'release': raven.fetch_git_sha(os.path.abspath(os.pardir)),
}

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} - {asctime} - {module} - {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            # 'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'formatter': 'verbose',
            'class': 'logging.StreamHandler',
        },
        'app': {
            'formatter': 'verbose',
            'class': 'logging.FileHandler',
            'filename': '/var/log/tolma.ch/app.log',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django.server': {
            'handlers': ['null'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['mail_admins',],
            'level': 'ERROR',
            'propagate': True,
        },
        'translations': {
            'level': 'INFO',
            'handlers': ['app'],
            'propagate': False,
        }
    }
}

AUTH_USER_MODEL = 'auth.User'

AUTOSLUG_SLUGIFY_FUNCTION = slugify.slugify

YANDEX_TRANSLATE_KEY = "***REMOVED***"

GLOSSARY_FILE_SIZE = 1048576
TM_FILE_SIZE = 104857600
DOCUMENT_FILE_SIZE = 104857600

GLOBAL_DOCUMENTS_DIR = "/var/www/tolmach_documents"
GLOBAL_DOCUMENTS_TMP_DIR = "/tmp"

ELASTIC_LIST = [
    {"host": "localhost", "port": 9200, "timeout": 30}
]

redis_host = os.environ.get('REDIS_HOST', 'redis')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{redis_host}:6379/2',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Channel layer definitions
# http://channels.readthedocs.org/en/latest/deploying.html#setting-up-a-channel-backend
CHANNEL_LAYERS = {
    "default": {
        # This example app uses the Redis channel layer implementation asgi_redis
        "BACKEND": "asgi_redis.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(redis_host, 6379)],
        },
       "ROUTING": "tolmach.routing.channel_routing", # We will create it in a moment
    },
}


from django.core.urlresolvers import reverse_lazy
LOGOUT_URL = reverse_lazy('loginas-logout')

DEBUG = os.environ.get("DEBUG", False) == 'True'
PROD = os.environ.get("PROD", False) == 'True'

try:
    from tolmach.local_settings import *
except ImportError:
    pass

MIDDLEWARE_CLASSES += (
    'social_django.middleware.SocialAuthExceptionMiddleware',
)

SOCIAL_AUTH_LOGIN_ERROR_URL = '/'
