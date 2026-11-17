import os

os.environ["DB_ENGINE"] = "django.db.backends.sqlite3"
os.environ["DB_NAME"] = ":memory:"
