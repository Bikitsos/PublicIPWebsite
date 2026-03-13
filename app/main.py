from __future__ import annotations

import ipaddress

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse


app = FastAPI(title="Public IP Website")

PUBLIC_IP_SERVICE_URL = "https://api.ipify.org?format=json"


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    if request.client and request.client.host:
        return request.client.host

    return "Unavailable"


def is_public_ip(value: str) -> bool:
    try:
        ip_address = ipaddress.ip_address(value)
    except ValueError:
        return False

    return not (
        ip_address.is_private
        or ip_address.is_loopback
        or ip_address.is_link_local
        or ip_address.is_reserved
        or ip_address.is_unspecified
    )


async def lookup_public_ip() -> str:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(PUBLIC_IP_SERVICE_URL)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError):
        return "Unavailable"

    ip_value = payload.get("ip", "Unavailable")
    if isinstance(ip_value, str):
        return ip_value

    return "Unavailable"


INDEX_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Public IP</title>
    <style>
      :root {
        color-scheme: light dark;
        --bg: #f4efe6;
        --panel: rgba(255, 252, 247, 0.92);
        --text: #1e1a16;
        --muted: #756a5f;
        --border: rgba(30, 26, 22, 0.1);
        --accent: #1e1a16;
        --accent-contrast: #fffaf4;
        --shadow: 0 24px 60px rgba(52, 40, 26, 0.12);
        --card-glow: linear-gradient(135deg, rgba(195, 144, 91, 0.08), transparent 45%);
        --ip-surface: rgba(255, 255, 255, 0.72);
        --ip-border: rgba(30, 26, 22, 0.08);
      }

      @media (prefers-color-scheme: dark) {
        :root:not([data-theme="light"]) {
          --bg: #13110f;
          --panel: rgba(28, 24, 21, 0.9);
          --text: #f3ebe0;
          --muted: #b7aa9b;
          --border: rgba(243, 235, 224, 0.08);
          --accent: #f1e5d5;
          --accent-contrast: #191512;
          --shadow: 0 28px 80px rgba(0, 0, 0, 0.34);
          --card-glow: linear-gradient(135deg, rgba(224, 171, 112, 0.12), transparent 45%);
          --ip-surface: rgba(255, 255, 255, 0.06);
          --ip-border: rgba(243, 235, 224, 0.1);
        }
      }

      :root[data-theme="dark"] {
        --bg: #13110f;
        --panel: rgba(28, 24, 21, 0.9);
        --text: #f3ebe0;
        --muted: #b7aa9b;
        --border: rgba(243, 235, 224, 0.08);
        --accent: #f1e5d5;
        --accent-contrast: #191512;
        --shadow: 0 28px 80px rgba(0, 0, 0, 0.34);
        --card-glow: linear-gradient(135deg, rgba(224, 171, 112, 0.12), transparent 45%);
        --ip-surface: rgba(255, 255, 255, 0.06);
        --ip-border: rgba(243, 235, 224, 0.1);
      }

      :root[data-theme="light"] {
        --bg: #f4efe6;
        --panel: rgba(255, 252, 247, 0.92);
        --text: #1e1a16;
        --muted: #756a5f;
        --border: rgba(30, 26, 22, 0.1);
        --accent: #1e1a16;
        --accent-contrast: #fffaf4;
        --shadow: 0 24px 60px rgba(52, 40, 26, 0.12);
        --card-glow: linear-gradient(135deg, rgba(195, 144, 91, 0.08), transparent 45%);
        --ip-surface: rgba(255, 255, 255, 0.72);
        --ip-border: rgba(30, 26, 22, 0.08);
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        padding: 24px;
        font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
        color: var(--text);
        background:
          radial-gradient(circle at top left, rgba(195, 144, 91, 0.22), transparent 30%),
          radial-gradient(circle at bottom right, rgba(109, 140, 120, 0.18), transparent 28%),
          linear-gradient(180deg, #f8f4ee 0%, var(--bg) 100%);
      }

      @media (prefers-color-scheme: dark) {
        body {
          background:
            radial-gradient(circle at top left, rgba(224, 171, 112, 0.16), transparent 28%),
            radial-gradient(circle at bottom right, rgba(90, 136, 120, 0.14), transparent 30%),
            linear-gradient(180deg, #181411 0%, var(--bg) 100%);
        }
      }

      :root[data-theme="dark"] body {
        background:
          radial-gradient(circle at top left, rgba(224, 171, 112, 0.16), transparent 28%),
          radial-gradient(circle at bottom right, rgba(90, 136, 120, 0.14), transparent 30%),
          linear-gradient(180deg, #181411 0%, var(--bg) 100%);
      }

      :root[data-theme="light"] body {
        background:
          radial-gradient(circle at top left, rgba(195, 144, 91, 0.22), transparent 30%),
          radial-gradient(circle at bottom right, rgba(109, 140, 120, 0.18), transparent 28%),
          linear-gradient(180deg, #f8f4ee 0%, var(--bg) 100%);
      }

      main {
        width: min(100%, 680px);
      }

      .card {
        position: relative;
        overflow: hidden;
        border: 1px solid var(--border);
        border-radius: 28px;
        padding: 32px;
        background: var(--panel);
        box-shadow: var(--shadow);
        backdrop-filter: blur(12px);
      }

      .card::before {
        content: "";
        position: absolute;
        inset: 0;
        background: var(--card-glow);
        pointer-events: none;
      }

      .eyebrow {
        margin: 0 0 8px;
        font-size: 0.8rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: var(--muted);
      }

      .header-row {
        display: flex;
        align-items: start;
        justify-content: space-between;
        gap: 16px;
      }

      .theme-toggle {
        padding: 10px 14px;
        border-radius: 999px;
        background: transparent;
        color: var(--text);
        border: 1px solid var(--border);
      }

      h1 {
        margin: 0;
        font-size: clamp(2rem, 4vw, 3.3rem);
        line-height: 0.95;
        font-weight: 700;
      }

      p {
        margin: 14px 0 0;
        max-width: 38ch;
        color: var(--muted);
        font-size: 1rem;
        line-height: 1.55;
      }

      .ip-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 28px;
        flex-wrap: wrap;
      }

      .ip-box {
        flex: 1 1 320px;
        min-width: 0;
        padding: 18px 20px;
        border-radius: 20px;
        background: var(--ip-surface);
        border: 1px solid var(--ip-border);
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
        font-size: clamp(1.1rem, 3vw, 1.5rem);
        letter-spacing: -0.04em;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      button {
        border: 0;
        border-radius: 999px;
        padding: 16px 20px;
        font: inherit;
        font-weight: 600;
        cursor: pointer;
        color: var(--accent-contrast);
        background: var(--accent);
        transition: transform 140ms ease, opacity 140ms ease;
      }

      button:hover {
        transform: translateY(-1px);
        opacity: 0.92;
      }

      button:active {
        transform: translateY(0);
      }

      .status {
        min-height: 1.3rem;
        margin-top: 14px;
        font-size: 0.95rem;
        color: var(--muted);
      }

      .support-row {
        margin-top: 24px;
      }

      .support-link {
        display: inline-flex;
        align-items: center;
      }

      .support-link img {
        display: block;
        height: 36px;
        border: 0;
      }

      @media (max-width: 640px) {
        .card {
          padding: 24px;
          border-radius: 24px;
        }

        .header-row {
          flex-direction: column;
          align-items: stretch;
        }

        .ip-row {
          align-items: stretch;
        }

        button {
          width: 100%;
        }
      }
    </style>
  </head>
  <body>
    <main>
      <section class="card">
        <div class="header-row">
          <div class="eyebrow">Network</div>
          <button id="theme-toggle" class="theme-toggle" type="button">Dark mode</button>
        </div>
        <h1>Your public IP</h1>
        <p>The address below is taken from the current request reaching this server.</p>
        <div class="ip-row">
          <div id="ip" class="ip-box" aria-live="polite">Loading...</div>
          <button id="copy-button" type="button">Copy</button>
        </div>
        <div id="status" class="status" aria-live="polite"></div>
        <div class="support-row">
          <a class="support-link" href="https://ko-fi.com/U7U21VX2BP" target="_blank" rel="noopener noreferrer">
            <img src="https://storage.ko-fi.com/cdn/kofi3.png?v=6" alt="Buy Me a Coffee at ko-fi.com" />
          </a>
        </div>
      </section>
    </main>
    <script>
      const themeStorageKey = "public-ip-theme";
      const rootElement = document.documentElement;
      const ipElement = document.getElementById("ip");
      const statusElement = document.getElementById("status");
      const copyButton = document.getElementById("copy-button");
      const themeToggleButton = document.getElementById("theme-toggle");

      let currentIp = "";

      function getPreferredTheme() {
        const savedTheme = window.localStorage.getItem(themeStorageKey);
        if (savedTheme === "light" || savedTheme === "dark") {
          return savedTheme;
        }

        return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      }

      function updateThemeLabel(theme) {
        themeToggleButton.textContent = theme === "dark" ? "Light mode" : "Dark mode";
      }

      function applyTheme(theme) {
        rootElement.dataset.theme = theme;
        window.localStorage.setItem(themeStorageKey, theme);
        updateThemeLabel(theme);
      }

      async function loadIp() {
        try {
          const response = await fetch("/api/ip", { headers: { "Accept": "application/json" } });
          if (!response.ok) {
            throw new Error("Request failed");
          }

          const payload = await response.json();
          currentIp = payload.ip || "Unavailable";
          ipElement.textContent = currentIp;
        } catch {
          currentIp = "Unavailable";
          ipElement.textContent = currentIp;
          statusElement.textContent = "Could not load the IP address.";
        }
      }

      copyButton.addEventListener("click", async () => {
        if (!currentIp || currentIp === "Unavailable") {
          statusElement.textContent = "Nothing to copy yet.";
          return;
        }

        try {
          await navigator.clipboard.writeText(currentIp);
          statusElement.textContent = "Copied to clipboard.";
        } catch {
          statusElement.textContent = "Clipboard access failed.";
        }
      });

      themeToggleButton.addEventListener("click", () => {
        const nextTheme = rootElement.dataset.theme === "dark" ? "light" : "dark";
        applyTheme(nextTheme);
      });

      applyTheme(getPreferredTheme());
      loadIp();
    </script>
  </body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return INDEX_HTML


@app.get("/api/ip", response_class=JSONResponse)
async def public_ip(request: Request) -> JSONResponse:
    client_ip = get_client_ip(request)
    if is_public_ip(client_ip):
        return JSONResponse({"ip": client_ip, "source": "request"})

    return JSONResponse({"ip": await lookup_public_ip(), "source": "lookup"})