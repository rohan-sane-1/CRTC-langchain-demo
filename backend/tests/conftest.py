import os

# Must be set before `app` is imported (Settings is read at import time).
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
os.environ.setdefault("SESSION_SECRET", "x" * 48)
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:3000")
os.environ.setdefault("ALLOWED_EMAILS", "me@example.com")
