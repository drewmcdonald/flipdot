# FlipDot Driver Installation Script for Raspberry Pi
# This script downloads, installs, and sets up the FlipDot driver to run on startup
#
# Usage: bash < (curl -fsSL https://raw.githubusercontent.com/drewmcdonald/flipdot/main/flipdot/install-rpi.sh)
#
# Or locally: bash install-rpi.sh

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FLIPDOT_HOME="${FLIPDOT_HOME:-/opt/flipdot}"
FLIPDOT_USER="${FLIPDOT_USER:-flipdot}"
FLIPDOT_VERSION="${FLIPDOT_VERSION:-latest}"
GITHUB_REPO="drewmcdonald/flipdot"
RELEASE_URL="https://api.github.com/repos/${GITHUB_REPO}/releases"

# Functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root"
        echo "Try running: sudo bash install-rpi.sh"
        exit 1
    fi
}

check_requirements() {
    log_info "Checking system requirements..."

    local missing_tools=()

    # Check for required commands
    for cmd in curl tar python3 systemctl; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_tools+=("$cmd")
        fi
    done

    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Installing missing dependencies..."
        apt-get update
        apt-get install -y "${missing_tools[@]}"
    fi

    # Check Python version
    if ! python3 --version | grep -q "3.11\|3.12\|3.13"; then
        log_warn "Python 3.11+ recommended ($(python3 --version) found)"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    log_success "System requirements met"
}

get_latest_release() {
    log_info "Fetching latest release information..."

    local download_url
    if [ "$FLIPDOT_VERSION" = "latest" ]; then
        download_url=$(curl -fsSL "$RELEASE_URL/latest" | grep '"browser_download_url"' | grep 'flipdot\.tar\.gz' | head -1 | cut -d'"' -f4 | tr -d '[:space:]')
        FLIPDOT_VERSION=$(curl -fsSL "$RELEASE_URL/latest" | grep '"tag_name"' | head -1 | cut -d'"' -f4 | tr -d '[:space:]')
    else
        download_url=$(curl -fsSL "$RELEASE_URL/tags/$FLIPDOT_VERSION" | grep '"browser_download_url"' | grep 'flipdot\.tar\.gz' | head -1 | cut -d'"' -f4 | tr -d '[:space:]')
    fi

    if [ -z "$download_url" ]; then
        log_error "Could not find release for version $FLIPDOT_VERSION"
        log_info "Available releases: $(curl -fsSL "$RELEASE_URL?per_page=5" | grep '"tag_name"' | cut -d'"' -f4)"
        exit 1
    fi

    echo "$download_url"
}

create_flipdot_user() {
    log_info "Setting up flipdot user..."

    if ! id "$FLIPDOT_USER" &>/dev/null; then
        useradd -r -s /usr/sbin/nologin -d /opt/flipdot "$FLIPDOT_USER"
        log_success "Created user: $FLIPDOT_USER"
    else
        log_success "User $FLIPDOT_USER already exists"
    fi
}

setup_directories() {
    log_info "Creating directories..."

    mkdir -p "$FLIPDOT_HOME"
    mkdir -p /var/log/flipdot
    mkdir -p /etc/flipdot

    chown -R "$FLIPDOT_USER:$FLIPDOT_USER" "$FLIPDOT_HOME"
    chown -R "$FLIPDOT_USER:$FLIPDOT_USER" /var/log/flipdot
    chmod 755 /etc/flipdot

    log_success "Directories created"
}

install_python_deps() {
    log_info "Installing Python dependencies..."

    # Check if venv module is available
    if ! python3 -m venv --help &>/dev/null; then
        log_info "Installing python3-venv..."
        apt-get install -y python3-venv
    fi

    # Create virtual environment
    python3 -m venv "$FLIPDOT_HOME/venv"

    # Activate and install packages
    source "$FLIPDOT_HOME/venv/bin/activate"
    pip install --upgrade pip setuptools wheel
    pip install pyserial pydantic
    deactivate

    log_success "Python dependencies installed in virtual environment"
}

download_release() {
    log_info "Downloading FlipDot $FLIPDOT_VERSION..."

    local download_url="$1"
    local temp_dir=$(mktemp -d)

    # Debug: print URL details
    log_info "Download URL: $download_url"
    log_info "URL length: ${#download_url}"

    if wget -q -O "$temp_dir/flipdot.tar.gz" "$download_url" 2>/dev/null || curl -fsSL -o "$temp_dir/flipdot.tar.gz" "$download_url"; then
        log_success "Download completed"

        # Extract to temporary location first
        tar -xzf "$temp_dir/flipdot.tar.gz" -C "$temp_dir"

        # Move to final location, preserving existing config if it exists
        if [ -f "$FLIPDOT_HOME/config.json" ]; then
            log_warn "Existing config.json found, preserving it"
            cp "$FLIPDOT_HOME/config.json" "$temp_dir/config.json.bak"
        fi

        # Copy application files
        cp -r "$temp_dir/flipdot" "$FLIPDOT_HOME/"
        cp -r "$temp_dir/README.md" "$FLIPDOT_HOME/" 2>/dev/null || true
        cp -r "$temp_dir/LICENSE" "$FLIPDOT_HOME/" 2>/dev/null || true

        # Restore config if it was backed up
        if [ -f "$temp_dir/config.json.bak" ]; then
            cp "$temp_dir/config.json.bak" "$FLIPDOT_HOME/config.json"
        fi

        # Set permissions
        chown -R "$FLIPDOT_USER:$FLIPDOT_USER" "$FLIPDOT_HOME"

        # Cleanup
        rm -rf "$temp_dir"

        log_success "Installation files extracted"
    else
        log_error "Failed to download release"
        rm -rf "$temp_dir"
        exit 1
    fi
}

create_config() {
    log_info "Setting up configuration..."

    if [ ! -f "$FLIPDOT_HOME/config.json" ]; then
        log_warn "No config.json found. Creating example configuration..."
        cat > "$FLIPDOT_HOME/config.json" << 'EOF'
{
  "poll_endpoint": "http://localhost:8000/api/flipdot/content",
  "poll_interval_ms": 30000,
  "enable_push": false,
  "push_port": 8080,
  "auth": {
    "type": "api_key",
    "key": "your-api-key-here",
    "header_name": "X-API-Key"
  },
  "serial_device": "/dev/ttyUSB0",
  "serial_baudrate": 57600,
  "module_layout": [[1], [2]],
  "module_width": 28,
  "module_height": 7,
  "error_fallback": "keep_last",
  "dev_mode": false,
  "log_level": "INFO"
}
EOF
        chown "$FLIPDOT_USER:$FLIPDOT_USER" "$FLIPDOT_HOME/config.json"
        chmod 600 "$FLIPDOT_HOME/config.json"

        log_warn "Please edit $FLIPDOT_HOME/config.json with your settings"
        log_info "Key settings to update:"
        echo "  - poll_endpoint: Your content server URL"
        echo "  - auth.key: Your API key"
        echo "  - serial_device: Your display serial device (/dev/ttyUSB0, etc.)"
        echo "  - module_layout: Your display configuration"
        echo ""
        read -p "Press enter to continue once you've updated the config..."
    else
        log_success "Config file already exists at $FLIPDOT_HOME/config.json"
    fi
}

create_systemd_service() {
    log_info "Creating systemd service..."

    cat > /etc/systemd/system/flipdot.service << EOF
[Unit]
Description=FlipDot Display Driver
Documentation=https://github.com/drewmcdonald/flipdot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$FLIPDOT_USER
WorkingDirectory=$FLIPDOT_HOME
ExecStart=$FLIPDOT_HOME/venv/bin/python -m flipdot.driver.main --config $FLIPDOT_HOME/config.json
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=flipdot

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$FLIPDOT_HOME /var/log/flipdot

[Install]
WantedBy=multi-user.target
EOF

    chmod 644 /etc/systemd/system/flipdot.service
    systemctl daemon-reload

    log_success "Systemd service created"
}

create_update_checker() {
    log_info "Creating update checker script..."

    cat > "$FLIPDOT_HOME/check-updates.sh" << 'EOF'
#!/bin/bash
# FlipDot Update Checker
# Checks for new releases and automatically updates if available
# Can be added to crontab: 0 * * * * /opt/flipdot/check-updates.sh

set -e

FLIPDOT_HOME="/opt/flipdot"
FLIPDOT_USER="flipdot"
GITHUB_REPO="drewmcdonald/flipdot"
RELEASE_URL="https://api.github.com/repos/${GITHUB_REPO}/releases"
VERSION_FILE="$FLIPDOT_HOME/.installed_version"

log_info() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1"; }
log_warn() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] WARN: $1"; }
log_error() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2; }

# Get installed version
if [ -f "$VERSION_FILE" ]; then
    INSTALLED_VERSION=$(cat "$VERSION_FILE")
else
    INSTALLED_VERSION="unknown"
fi

# Get latest version
LATEST_VERSION=$(curl -fsSL "$RELEASE_URL/latest" 2>/dev/null | grep '"tag_name"' | head -1 | cut -d'"' -f4)

if [ -z "$LATEST_VERSION" ]; then
    log_error "Could not fetch latest version"
    exit 1
fi

log_info "Installed: $INSTALLED_VERSION | Latest: $LATEST_VERSION"

if [ "$INSTALLED_VERSION" = "$LATEST_VERSION" ]; then
    log_info "Already up to date"
    exit 0
fi

log_warn "Update available: $INSTALLED_VERSION → $LATEST_VERSION"

# Only auto-update if explicitly enabled via environment variable
if [ "$FLIPDOT_AUTO_UPDATE" = "true" ]; then
    log_info "Auto-update enabled, installing..."

    # Download and extract
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT

    DOWNLOAD_URL=$(curl -fsSL "$RELEASE_URL/tags/$LATEST_VERSION" | grep '"browser_download_url"' | grep 'flipdot\.tar\.gz' | head -1 | cut -d'"' -f4 | tr -d '[:space:]')

    if [ -z "$DOWNLOAD_URL" ]; then
        log_error "Could not find RPi release asset"
        exit 1
    fi

    if curl -fsSL -o "$TEMP_DIR/flipdot.tar.gz" "$DOWNLOAD_URL"; then
        tar -xzf "$TEMP_DIR/flipdot.tar.gz" -C "$TEMP_DIR"

        # Backup current version
        if [ -d "$FLIPDOT_HOME/flipdot" ]; then
            cp -r "$FLIPDOT_HOME/flipdot" "$FLIPDOT_HOME/flipdot.backup"
        fi

        # Install new version
        cp -r "$TEMP_DIR/flipdot" "$FLIPDOT_HOME/"
        cp "$TEMP_DIR/README.md" "$FLIPDOT_HOME/" 2>/dev/null || true
        chown -R "$FLIPDOT_USER:$FLIPDOT_USER" "$FLIPDOT_HOME/flipdot"

        # Update version file
        echo "$LATEST_VERSION" > "$VERSION_FILE"

        # Restart service
        systemctl restart flipdot
        log_info "Updated to $LATEST_VERSION and restarted service"
    else
        log_error "Failed to download update"
        exit 1
    fi
else
    log_info "Auto-update not enabled. To enable, set FLIPDOT_AUTO_UPDATE=true"
fi
EOF

    chmod +x "$FLIPDOT_HOME/check-updates.sh"
    chown "$FLIPDOT_USER:$FLIPDOT_USER" "$FLIPDOT_HOME/check-updates.sh"

    log_success "Update checker created at $FLIPDOT_HOME/check-updates.sh"
}

setup_cron() {
    log_info "Setting up automatic update checker..."

    local cron_job="0 * * * * $FLIPDOT_HOME/check-updates.sh >> /var/log/flipdot/updates.log 2>&1"
    local cron_temp=$(mktemp)

    # Get current crontab for flipdot user or create empty
    crontab -u "$FLIPDOT_USER" -l > "$cron_temp" 2>/dev/null || echo "" > "$cron_temp"

    # Add our job if it doesn't exist
    if ! grep -q "check-updates.sh" "$cron_temp"; then
        echo "$cron_job" >> "$cron_temp"
        crontab -u "$FLIPDOT_USER" "$cron_temp"
        log_success "Hourly update checker scheduled"
    fi

    rm -f "$cron_temp"
}

enable_and_start() {
    log_info "Enabling and starting flipdot service..."

    systemctl enable flipdot
    systemctl start flipdot

    sleep 2

    if systemctl is-active --quiet flipdot; then
        log_success "FlipDot service started successfully"
    else
        log_error "FlipDot service failed to start"
        log_info "Check logs with: journalctl -u flipdot -n 50"
        exit 1
    fi
}

show_status() {
    log_info "Current service status:"
    systemctl status flipdot --no-pager

    echo ""
    log_info "Recent logs:"
    journalctl -u flipdot -n 20 --no-pager
}

show_next_steps() {
    echo ""
    echo -e "${GREEN}Installation Complete!${NC}"
    echo ""
    log_info "Next steps:"
    echo "  1. Edit configuration: sudo nano $FLIPDOT_HOME/config.json"
    echo "  2. Set your content server URL and API key"
    echo "  3. Set your serial device (e.g., /dev/ttyUSB0)"
    echo ""
    log_info "Useful commands:"
    echo "  - View logs:         journalctl -u flipdot -f"
    echo "  - Check status:      systemctl status flipdot"
    echo "  - Restart service:   systemctl restart flipdot"
    echo "  - Stop service:      systemctl stop flipdot"
    echo "  - View config:       cat $FLIPDOT_HOME/config.json"
    echo "  - Check for updates: $FLIPDOT_HOME/check-updates.sh"
    echo ""
    log_info "Enable auto-updates (hourly check): FLIPDOT_AUTO_UPDATE=true $FLIPDOT_HOME/check-updates.sh"
    echo ""
}

# Main installation flow
main() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════╗"
    echo "║   FlipDot Driver Installation Script   ║"
    echo "║         for Raspberry Pi                ║"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""

    check_root
    check_requirements
    create_flipdot_user
    setup_directories
    install_python_deps

    local download_url=$(get_latest_release)
    download_release "$download_url"

    create_config
    create_systemd_service
    create_update_checker
    setup_cron
    enable_and_start
    show_status
    show_next_steps
}

# Run main function
main
