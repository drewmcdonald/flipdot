#!/usr/bin/env bash
# FlipDot driver installer for Raspberry Pi (single-binary Rust port).
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/drewmcdonald/flipdot/main/driver-rs/install-rpi.sh | sudo bash
#
# Environment variables:
#   FLIPDOT_VERSION   Release tag to install (default: latest)
#   FLIPDOT_HOME      Install directory (default: /opt/flipdot)
#   FLIPDOT_USER      Service user (default: flipdot)

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_info()    { echo -e "${BLUE}i${NC} $1" >&2; }
log_success() { echo -e "${GREEN}+${NC} $1" >&2; }
log_warn()    { echo -e "${YELLOW}!${NC} $1" >&2; }
log_error()   { echo -e "${RED}x${NC} $1" >&2; }

FLIPDOT_HOME="${FLIPDOT_HOME:-/opt/flipdot}"
FLIPDOT_USER="${FLIPDOT_USER:-flipdot}"
FLIPDOT_VERSION="${FLIPDOT_VERSION:-latest}"
GITHUB_REPO="drewmcdonald/flipdot"
RELEASE_URL="https://api.github.com/repos/${GITHUB_REPO}/releases"

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Run as root (sudo bash install-rpi.sh)"
        exit 1
    fi
}

detect_arch() {
    local arch
    arch="$(uname -m)"
    case "$arch" in
        aarch64|arm64) echo "aarch64-unknown-linux-gnu" ;;
        armv7l)        echo "armv7-unknown-linux-gnueabihf" ;;
        x86_64)        echo "x86_64-unknown-linux-gnu" ;;
        *)
            log_error "Unsupported architecture: $arch"
            exit 1
            ;;
    esac
}

require_cmd() {
    for cmd in "$@"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            log_error "Missing required tool: $cmd"
            log_info "Install with: apt-get install -y $cmd"
            exit 1
        fi
    done
}

find_release_asset() {
    local target="$1"
    local api_url
    if [ "$FLIPDOT_VERSION" = "latest" ]; then
        api_url="$RELEASE_URL/latest"
    else
        api_url="$RELEASE_URL/tags/$FLIPDOT_VERSION"
    fi
    curl -fsSL "$api_url" \
        | grep '"browser_download_url"' \
        | grep "flipdot-${target}" \
        | head -1 \
        | cut -d'"' -f4 \
        | tr -d '[:space:]'
}

create_user() {
    if ! id "$FLIPDOT_USER" &>/dev/null; then
        useradd -r -s /usr/sbin/nologin -d "$FLIPDOT_HOME" "$FLIPDOT_USER"
        log_success "created user $FLIPDOT_USER"
    fi
    usermod -a -G dialout "$FLIPDOT_USER"
}

install_binary() {
    local target="$1"
    local url
    url="$(find_release_asset "$target")"
    if [ -z "$url" ]; then
        log_error "no release asset for target $target (version $FLIPDOT_VERSION)"
        exit 1
    fi
    log_info "downloading $url"
    mkdir -p "$FLIPDOT_HOME/bin"
    local tmp
    tmp="$(mktemp)"
    curl -fsSL -o "$tmp" "$url"
    install -m 0755 "$tmp" "$FLIPDOT_HOME/bin/flipdot"
    rm -f "$tmp"
    chown -R "$FLIPDOT_USER:$FLIPDOT_USER" "$FLIPDOT_HOME"
    log_success "installed $FLIPDOT_HOME/bin/flipdot"
}

ensure_config() {
    if [ -f "$FLIPDOT_HOME/config.json" ]; then
        log_info "preserving existing $FLIPDOT_HOME/config.json"
        return
    fi
    cat > "$FLIPDOT_HOME/config.json" <<'EOF'
{
  "convex_url": "https://your-deployment.convex.cloud",
  "display_name": "main",
  "serial_device": "/dev/ttyUSB0",
  "serial_baudrate": 57600,
  "module_layout": [[1], [2]],
  "module_width": 28,
  "module_height": 7,
  "dev_mode": false,
  "log_level": "INFO"
}
EOF
    chown "$FLIPDOT_USER:$FLIPDOT_USER" "$FLIPDOT_HOME/config.json"
    chmod 600 "$FLIPDOT_HOME/config.json"
    log_warn "wrote template config; edit $FLIPDOT_HOME/config.json before starting"
}

install_service() {
    cat > /etc/systemd/system/flipdot.service <<EOF
[Unit]
Description=FlipDot Display Driver
Documentation=https://github.com/${GITHUB_REPO}
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${FLIPDOT_USER}
WorkingDirectory=${FLIPDOT_HOME}
ExecStart=${FLIPDOT_HOME}/bin/flipdot --config ${FLIPDOT_HOME}/config.json
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=flipdot

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${FLIPDOT_HOME}
MemoryMax=128M
CPUQuota=25%

[Install]
WantedBy=multi-user.target
EOF
    chmod 644 /etc/systemd/system/flipdot.service
    systemctl daemon-reload
    log_success "installed systemd unit"
}

main() {
    check_root
    require_cmd curl install useradd usermod systemctl
    mkdir -p "$FLIPDOT_HOME"
    create_user
    local target
    target="$(detect_arch)"
    log_info "target: $target"
    install_binary "$target"
    ensure_config
    install_service
    systemctl enable flipdot
    log_success "installation complete"
    log_info  "edit $FLIPDOT_HOME/config.json, then:  systemctl start flipdot"
}

main "$@"
