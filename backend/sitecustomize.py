import os

# Avoid third-party pytest plugin auto-load issues in this repo's environment.
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
