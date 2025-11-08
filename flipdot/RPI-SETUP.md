# Raspberry Pi FlipDot Driver Setup

Complete automated setup for running the FlipDot driver on a Raspberry Pi with automatic updates and systemd daemon management.

## Quick Start (One Command)

```bash
sudo bash <(curl -fsSL https://raw.githubusercontent.com/drewmcdonald/flipdot/main/flipdot/install-rpi.sh)
```

Or if you have the script locally:

```bash
sudo bash install-rpi.sh
```

## What the Installation Script Does

The `install-rpi.sh` script automatically:

1. **Checks system requirements** - Verifies Python 3.11+ and required tools
2. **Creates flipdot user** - Non-privileged user for running the service
3. **Sets up directories** - Creates `/opt/flipdot`, `/var/log/flipdot`, etc.
4. **Installs Python dependencies** - Creates a virtual environment and installs pyserial & pydantic
5. **Downloads the latest release** - Fetches the RPi-specific distribution from GitHub
6. **Creates configuration template** - Sets up an example config file
7. **Installs systemd service** - Creates a daemon that runs on startup
8. **Sets up update checker** - Configures hourly update checks via cron
9. **Starts the service** - Enables and starts the flipdot daemon

## Configuration

After installation, edit your configuration:

```bash
sudo nano /opt/flipdot/config.json
```

### Required Settings

- **poll_endpoint**: Your FlipDot content server URL
  - Example: `http://192.168.1.100:8000/api/flipdot/content`

- **auth.key**: Your API key for authentication
  - Example: `"secret-api-key-12345"`

- **serial_device**: Your display serial connection
  - Common: `/dev/ttyUSB0` for USB, `/dev/ttyAMA0` for GPIO UART
  - Find your device: `ls /dev/tty*`

- **module_layout**: Your display configuration (grid of modules)
  - Example for 2x7 display: `[[1], [2]]` (two modules stacked vertically)
  - Example for 4 modules in 2x2: `[[1, 2], [3, 4]]`

- **module_width** / **module_height**: Size of each module in pixels
  - Typical: 28x7 pixels per module

### Optional Settings

- **poll_interval_ms**: How often to check for updates (default: 30000ms)
- **enable_push**: Enable push notification server (default: false)
- **push_port**: Port for push server if enabled (default: 8080)
- **error_fallback**: What to show on error - "keep_last" or "blank"
- **log_level**: Logging verbosity - "DEBUG", "INFO", "WARNING", "ERROR"

## Managing the Service

### View status
```bash
systemctl status flipdot
```

### View logs
```bash
# Last 50 lines
journalctl -u flipdot -n 50

# Follow live logs
journalctl -u flipdot -f

# Logs from last hour
journalctl -u flipdot --since "1 hour ago"
```

### Start/Stop/Restart
```bash
systemctl start flipdot      # Start the service
systemctl stop flipdot       # Stop the service
systemctl restart flipdot    # Restart the service
systemctl enable flipdot     # Enable on boot (default)
systemctl disable flipdot    # Disable on boot
```

## Updates

The installation creates an automatic update checker that runs hourly. It will:

- Check for new releases on GitHub
- Download if a new version is available
- Log activity to `/var/log/flipdot/updates.log`

### Manual Update Check
```bash
/opt/flipdot/check-updates.sh
```

### Enable Auto-Updates
By default, the update checker only notifies you. To enable automatic updates:

```bash
sudo bash -c 'echo "export FLIPDOT_AUTO_UPDATE=true" >> /etc/environment'
```

Or run updates manually when you see them available.

### View Update Logs
```bash
sudo cat /var/log/flipdot/updates.log
```

## Troubleshooting

### Service won't start
```bash
# Check the logs
journalctl -u flipdot -n 50

# Common issues:
# - Config file doesn't exist or is invalid JSON
# - Serial device not found (/dev/ttyUSB0 doesn't exist)
# - API key is incorrect
# - Content server is unreachable
```

### Can't find serial device
```bash
# List all serial devices
ls /dev/tty*

# Check permissions
ls -la /dev/ttyUSB0

# If permission denied, add flipdot user to dialout group
sudo usermod -a -G dialout flipdot
sudo systemctl restart flipdot
```

### Update checker not running
```bash
# Check if cron job exists
sudo crontab -u flipdot -l

# Test the update script manually
/opt/flipdot/check-updates.sh
```

### Display not updating
1. Check that `poll_endpoint` is correct and reachable
2. Verify API key is correct in config
3. Verify serial device is correct
4. Add the flipdot user to the dialout group (see above)
5. Check logs: `journalctl -u flipdot -f`

## File Locations

- **Application**: `/opt/flipdot/`
- **Configuration**: `/opt/flipdot/config.json`
- **Driver code**: `/opt/flipdot/flipdot/`
- **Logs**: `/var/log/flipdot/`
- **Service file**: `/etc/systemd/system/flipdot.service`
- **Update checker**: `/opt/flipdot/check-updates.sh`
- **Virtual environment**: `/opt/flipdot/venv/`
- **Installed version**: `/opt/flipdot/.installed_version`

## Uninstallation

To completely remove FlipDot:

```bash
# Stop and disable service
sudo systemctl stop flipdot
sudo systemctl disable flipdot

# Remove cron jobs
sudo crontab -u flipdot -r

# Remove application
sudo rm -rf /opt/flipdot
sudo rm -rf /var/log/flipdot
sudo rm -f /etc/systemd/system/flipdot.service
sudo systemctl daemon-reload

# Remove user
sudo userdel flipdot

# Remove group
sudo groupdel flipdot
```

## Development / Custom Builds

If you're developing the driver locally and want to test on RPi:

```bash
# Transfer and run local script
scp install-rpi.sh pi@raspberrypi.local:~/
ssh pi@raspberrypi.local
sudo bash ~/install-rpi.sh

# Or specify a development version
FLIPDOT_VERSION=dev-branch bash install-rpi.sh
```

## Architecture

The installation creates a production-ready setup:

```
Raspberry Pi
├── systemd service (flipdot.service)
│   └── Runs continuously with auto-restart
├── Python virtual environment (/opt/flipdot/venv/)
│   └── Isolated dependencies (pyserial, pydantic)
├── Application code (/opt/flipdot/flipdot/)
│   └── Driver entry point: main.py
├── Update checker (cron job, hourly)
│   └── Checks GitHub releases, optionally auto-updates
└── Logs (journald)
    └── Accessible via journalctl

Polling Behavior
├── Polls content server every 30 seconds
├── Renders received content to display
├── Falls back to last valid frame on error
└── Exponential backoff on network failures
```

## Security Notes

- The flipdot user is non-privileged and has restricted file access
- Config file is readable only by the flipdot user (mode 600)
- Systemd service runs with security hardening:
  - No new privileges
  - Private /tmp
  - Read-only root filesystem
  - Limited memory (512MB) and CPU (50%)

## Getting Help

- Check logs: `journalctl -u flipdot -f`
- Review config: `/opt/flipdot/config.json`
- GitHub issues: https://github.com/drewmcdonald/flipdot/issues

## Release Notes

The installation script will install the latest release from GitHub. See the release notes for changes:
https://github.com/drewmcdonald/flipdot/releases
