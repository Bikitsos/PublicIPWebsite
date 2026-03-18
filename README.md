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

## Deploy to Fedora with Cloudflare Tunnel

This project includes a helper script that builds the app image and runs two containers in the same Podman pod:

- the FastAPI app
- `cloudflared`

That means `cloudflared` can reach the app over `http://localhost:8000` inside the pod, and you do not need to publish any server port.

1. Create a Cloudflare Tunnel in the Cloudflare dashboard.
2. In the tunnel public hostname settings, set the service URL to `http://localhost:8000`.
3. Run the helper script on your Fedora server from this repository:

```bash
chmod +x scripts/install-fedora-cloudflare.sh
CF_TUNNEL_TOKEN=your-token ./scripts/install-fedora-cloudflare.sh
```

The script will install Podman with `dnf` if needed, rebuild the local app image, recreate the Podman pod, generate systemd user units for the pod, and enable them so the stack starts again after reboot.

Restart behavior is intentionally managed by systemd, not by Podman container restart flags. That avoids the common failure mode where generated units and `--restart` policies fight each other during shutdown or boot, which can leave `cloudflared` stopped after a restart.

It also attempts to enable `loginctl` lingering for the current user, which is required on Fedora for user-level systemd services to come back automatically after boot.
