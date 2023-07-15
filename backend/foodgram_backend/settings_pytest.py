from .databases import DATABASE_SQLITE_PYTEST
from .settings import *

DATABASES = DATABASE_SQLITE_PYTEST

SECRET_KEY = 'test_secret_key'

MEDIA_ROOT = BASE_DIR / 'foodgram_app/test_media'
