import os

# Run Qt tests without a display server.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
