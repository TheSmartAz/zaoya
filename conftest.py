import os

# Prevent third-party pytest plugins (e.g., langsmith) from auto-loading in this repo.
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
