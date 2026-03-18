# Development Status

## 2026-03-18

- Fixed the Fedora Cloudflare deployment script so restart handling is owned by systemd instead of conflicting with Podman container `--restart` policies.
- Added explicit generated unit restart settings: `SYSTEMD_RESTART_POLICY=always` and `SYSTEMD_RESTART_SEC=10`.
- Updated deployment documentation to explain why this change prevents `cloudflared` from staying down after a reboot.
- Validation completed with `bash -n scripts/install-fedora-cloudflare.sh` and workspace diagnostics.