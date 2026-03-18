#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_DIR=$(cd -- "${SCRIPT_DIR}/.." && pwd)

POD_NAME=${POD_NAME:-public-ip-stack}
APP_IMAGE=${APP_IMAGE:-localhost/public-ip-website:latest}
APP_CONTAINER_NAME=${APP_CONTAINER_NAME:-public-ip-website}
CF_CONTAINER_NAME=${CF_CONTAINER_NAME:-public-ip-cloudflared}
CF_IMAGE=${CF_IMAGE:-docker.io/cloudflare/cloudflared:latest}
CF_TUNNEL_TOKEN=${CF_TUNNEL_TOKEN:-}
SYSTEMD_USER_DIR=${XDG_CONFIG_HOME:-${HOME}/.config}/systemd/user
SYSTEMD_POD_UNIT=${SYSTEMD_POD_UNIT:-pod-${POD_NAME}.service}
SYSTEMD_RESTART_POLICY=${SYSTEMD_RESTART_POLICY:-always}
SYSTEMD_RESTART_SEC=${SYSTEMD_RESTART_SEC:-10}

require_command() {
    if command -v "$1" >/dev/null 2>&1; then
        return 0
    fi

    echo "Missing required command: $1" >&2
    exit 1
}

ensure_podman() {
    if command -v podman >/dev/null 2>&1; then
        return 0
    fi

    if ! command -v sudo >/dev/null 2>&1; then
        echo "podman is not installed and sudo is unavailable." >&2
        exit 1
    fi

    if ! command -v dnf >/dev/null 2>&1; then
        echo "This installer expects Fedora with dnf available." >&2
        exit 1
    fi

    echo "Installing podman with dnf..."
    sudo dnf install -y podman
}

ensure_token() {
    if [[ -n "${CF_TUNNEL_TOKEN}" ]]; then
        return 0
    fi

    cat >&2 <<'EOF'
CF_TUNNEL_TOKEN is required.

Create a Cloudflare Tunnel in the dashboard, then run this script like:

  CF_TUNNEL_TOKEN=your-token ./scripts/install-fedora-cloudflare.sh

In the Cloudflare Tunnel public hostname settings, point the service to:

  http://localhost:8000

Because cloudflared runs in the same Podman pod as the app, no server port needs to be opened.
EOF
    exit 1
}

ensure_systemd() {
    require_command systemctl
}

enable_linger() {
    if ! command -v loginctl >/dev/null 2>&1; then
        echo "loginctl is not available. Skipping linger setup." >&2
        return 0
    fi

    if loginctl show-user "${USER}" -p Linger 2>/dev/null | grep -q 'Linger=yes'; then
        return 0
    fi

    if command -v sudo >/dev/null 2>&1; then
        echo "Enabling user lingering so systemd user services start on reboot..."
        sudo loginctl enable-linger "${USER}"
        return 0
    fi

    cat >&2 <<EOF
User lingering is not enabled, so user services may not start automatically after reboot.

Run this once as a privileged user on the Fedora server:

  loginctl enable-linger ${USER}
EOF
}


disable_existing_service() {
    if systemctl --user list-unit-files "${SYSTEMD_POD_UNIT}" >/dev/null 2>&1; then
        systemctl --user disable --now "${SYSTEMD_POD_UNIT}" >/dev/null 2>&1 || true
    fi
}

remove_existing_stack() {
    if podman pod exists "${POD_NAME}"; then
        echo "Removing existing pod ${POD_NAME}..."
        podman pod rm -f "${POD_NAME}"
    fi
}

install_systemd_units() {
    local temp_dir

    temp_dir=$(mktemp -d)
    mkdir -p "${SYSTEMD_USER_DIR}"

    echo "Generating systemd user units..."
    (
        cd "${temp_dir}"
        podman generate systemd \
            --new \
            --files \
            --name "${POD_NAME}" \
            --restart-policy "${SYSTEMD_RESTART_POLICY}" \
            --restart-sec "${SYSTEMD_RESTART_SEC}"
    )

    mv "${temp_dir}/pod-${POD_NAME}.service" "${SYSTEMD_USER_DIR}/"
    mv "${temp_dir}/container-${APP_CONTAINER_NAME}.service" "${SYSTEMD_USER_DIR}/"
    mv "${temp_dir}/container-${CF_CONTAINER_NAME}.service" "${SYSTEMD_USER_DIR}/"
    rm -rf "${temp_dir}"

    echo "Handing the stack over to systemd..."
    podman pod rm -f "${POD_NAME}"

    echo "Reloading and enabling ${SYSTEMD_POD_UNIT}..."
    systemctl --user daemon-reload
    systemctl --user enable --now "${SYSTEMD_POD_UNIT}"
}

main() {
    ensure_podman
    ensure_systemd
    require_command git
    ensure_token
    enable_linger

    cd "${PROJECT_DIR}"

    echo "Building application image ${APP_IMAGE}..."
    podman build -t "${APP_IMAGE}" -f Containerfile .

    disable_existing_service
    remove_existing_stack

    echo "Creating pod ${POD_NAME}..."
    podman pod create --name "${POD_NAME}"

    echo "Starting application container ${APP_CONTAINER_NAME}..."
    podman run -d \
        --name "${APP_CONTAINER_NAME}" \
        --pod "${POD_NAME}" \
        "${APP_IMAGE}"

    echo "Starting cloudflared container ${CF_CONTAINER_NAME}..."
    podman run -d \
        --name "${CF_CONTAINER_NAME}" \
        --pod "${POD_NAME}" \
        --pull always \
        "${CF_IMAGE}" \
        tunnel --no-autoupdate run --token "${CF_TUNNEL_TOKEN}"

    install_systemd_units

    echo
    echo "Deployment complete."
    echo "Pod status:"
    podman pod ps --filter "name=${POD_NAME}"
    echo
    echo "Container status:"
    podman ps --filter "pod=${POD_NAME}"
    echo
    echo "Configure the Cloudflare Tunnel public hostname service as http://localhost:8000."
    echo "No host port is published by this script."
    echo "The Podman pod is installed as a systemd user service and is enabled to start on reboot."
}

main "$@"