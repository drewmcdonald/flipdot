# Raspberry Pi FlipDot - Quick Reference

## Installation (One Command)

```bash
sudo bash <(curl -fsSL https://raw.githubusercontent.com/drewmcdonald/flipdot/main/install-rpi.sh)
```

Then edit config:
```bash
sudo nano /opt/flipdot/config.json
```

## Essential Commands

| Task | Command |
|------|---------|
| Check status | `systemctl status flipdot` |
| View logs (live) | `journalctl -u flipdot -f` |
| View logs (last 50) | `journalctl -u flipdot -n 50` |
| Restart service | `sudo systemctl restart flipdot` |
| Stop service | `sudo systemctl stop flipdot` |
| Start service | `sudo systemctl start flipdot` |
| Check for updates | `/opt/flipdot/check-updates.sh` |
| Edit config | `sudo nano /opt/flipdot/config.json` |

## Critical Config Settings

```json
{
  "poll_endpoint": "http://your-server:8000/api/flipdot/content",
  "auth": {
    "key": "your-api-key-here"
  },
  "serial_device": "/dev/ttyUSB0"
}
```

**Find your serial device:**
```bash
ls /dev/tty*
```

## Permissions Issue Fix

If you get "permission denied" for serial device:

```bash
sudo usermod -a -G dialout flipdot
sudo systemctl restart flipdot
```

## Update Configuration

Edit `/etc/environment`:
```bash
sudo nano /etc/environment
```

Add this line to enable auto-updates:
```
FLIPDOT_AUTO_UPDATE=true
```

Restart to apply:
```bash
sudo reboot
```

## File Locations

| Item | Path |
|------|------|
| Config | `/opt/flipdot/config.json` |
| Logs | Journal: `journalctl -u flipdot -f` |
| Update logs | `/var/log/flipdot/updates.log` |
| App code | `/opt/flipdot/flipdot/` |
| Service file | `/etc/systemd/system/flipdot.service` |
| Update script | `/opt/flipdot/check-updates.sh` |

## Debugging

```bash
# Test config validity
python3 -c "import json; json.load(open('/opt/flipdot/config.json'))" && echo "Config OK"

# Check service errors
systemctl status flipdot

# Check serial port connection
ls -la /dev/ttyUSB0

# Test network to server
curl -H "X-API-Key: your-key" http://your-server:8000/api/flipdot/content

# Full logs with timestamps
journalctl -u flipdot --output=verbose
```

## Common Issues & Fixes

| Problem | Solution |
|---------|----------|
| Serial port not found | Run `ls /dev/tty*` to find device, update config |
| Permission denied on serial | `sudo usermod -a -G dialout flipdot && sudo systemctl restart flipdot` |
| "Connection refused" | Verify server URL in config, check if server is running |
| Invalid API key error | Update `auth.key` in config with correct key |
| Service won't start | Check logs: `journalctl -u flipdot -n 50` |

## Service Operations

```bash
# Enable auto-start on boot (default after install)
sudo systemctl enable flipdot

# Disable auto-start
sudo systemctl disable flipdot

# Reload service files after editing
sudo systemctl daemon-reload

# Completely uninstall
sudo systemctl stop flipdot
sudo systemctl disable flipdot
sudo rm -rf /opt/flipdot
sudo rm /etc/systemd/system/flipdot.service
sudo systemctl daemon-reload
sudo userdel flipdot
```

## Log Examples

**Successful startup:**
```
Nov 07 14:23:45 raspberrypi flipdot[1234]: Starting FlipDot driver...
Nov 07 14:23:45 raspberrypi flipdot[1234]: Connected to /dev/ttyUSB0
Nov 07 14:23:45 raspberrypi flipdot[1234]: Polling http://localhost:8000/api/flipdot/content
Nov 07 14:23:45 raspberrypi flipdot[1234]: Rendering frame 0/5
```

**Config error:**
```
Nov 07 14:23:45 raspberrypi flipdot[1234]: Error: Config validation failed
Nov 07 14:23:45 raspberrypi flipdot[1234]: Missing required field: poll_endpoint
```

**Connection error:**
```
Nov 07 14:23:45 raspberrypi flipdot[1234]: Connection refused to http://localhost:8000
Nov 07 14:23:45 raspberrypi flipdot[1234]: Retrying in 10s...
```

## Version Management

```bash
# Check which version is installed
cat /opt/flipdot/.installed_version

# View available versions
curl -s https://api.github.com/repos/drewmcdonald/flipdot/releases?per_page=5 | grep tag_name

# Manual update (if not auto-updating)
/opt/flipdot/check-updates.sh
```

## For Developers

```bash
# Run driver manually for testing
source /opt/flipdot/venv/bin/activate
python -m flipdot.driver.main --config /opt/flipdot/config.json

# Run in dev mode (no hardware required)
python -m flipdot.driver.main --config /opt/flipdot/config.dev.json

# Check Python version
python --version
```

## Resources

- **GitHub**: https://github.com/drewmcdonald/flipdot
- **Issues**: https://github.com/drewmcdonald/flipdot/issues
- **Releases**: https://github.com/drewmcdonald/flipdot/releases
- **Server docs**: Check `CONTENT_SERVER_SPEC.md` in the repository

## Pro Tips

1. **Backup your config** before updating:
   ```bash
   sudo cp /opt/flipdot/config.json /opt/flipdot/config.json.bak
   ```

2. **Test config changes** before restarting:
   ```bash
   python3 -c "import json; json.load(open('/opt/flipdot/config.json'))" && echo "Valid"
   ```

3. **Monitor in real-time** while testing:
   ```bash
   journalctl -u flipdot -f
   ```

4. **Keep logs clean** by restarting regularly:
   ```bash
   sudo systemctl restart flipdot
   ```

5. **Check before pulling the plug**:
   ```bash
   systemctl status flipdot
   ```
