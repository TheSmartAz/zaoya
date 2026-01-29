# Run Backend Locally (Dev)

This repo expects the backend migrations to be applied and the API to run with auth bypass in dev.

## 1) Run migrations

```bash
cd /Users/thesmartaz/Qoder-Project/zaoya/backend
alembic upgrade head
```

## 2) Start the API with auth bypass

```bash
cd /Users/thesmartaz/Qoder-Project/zaoya/backend
ZAOYA_BYPASS_AUTH=1 uvicorn app.main:app --reload
```

## Notes

- `ZAOYA_BYPASS_AUTH=1` enables the dev user and skips token auth.
- You can stop the server with Ctrl+C in the terminal.
- If you prefer a different host/port, pass `--host` / `--port` to `uvicorn`.

