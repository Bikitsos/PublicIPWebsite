# Public IP Website

Minimal FastAPI app that displays the visitor IP address and provides a copy button.

When the app is accessed through localhost during development, it falls back to a public IP lookup service so you still see your outward-facing IP instead of `127.0.0.1`.

## Run locally with uv

```bash
uv sync
uv run uvicorn app.main:app --reload
```

The app will be available at `http://127.0.0.1:8000`.

## Build and run with Podman

```bash
podman build -t public-ip-website -f Containerfile .
podman run --rm -p 8000:8000 public-ip-website
```

Then open `http://127.0.0.1:8000`.