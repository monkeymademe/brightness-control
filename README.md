# Raspberry Pi Backlight Control Widget

A brightness control widget for the official Raspberry Pi 5-inch touch screen, designed for Raspberry Pi OS Bookworm and Trixie.

## Features

- **Brightness Slider**: Adjust backlight brightness from 0-100%
- **Current Value Display**: Shows brightness percentage and raw value
- **Backlight On/Off**: Toggle backlight completely off
- **Double-Tap Wake**: When backlight is off, double-tap anywhere on the screen to restore brightness
- **Panel Integration**: Add to wf-panel-pi taskbar for easy access
- **Auto-Start**: Automatically starts on boot via systemd

## Requirements

- Raspberry Pi OS Bookworm (Debian 12) or Trixie (Debian 13)
- Official Raspberry Pi touch screen
- Wayland desktop environment with wf-panel-pi (default on Raspberry Pi OS)
- Python 3.11+

## Installation

1. Navigate to the brightness-control directory:
   ```bash
   cd ~/brightness-control
   ```

2. Run the installation script:
   ```bash
   ./install.sh
   ```

3. **Important**: Log out and log back in for group changes to take effect.

4. Add the widget to your panel (choose one method):

   **Method 1 - Automatic (Recommended):**
   ```bash
   ~/brightness-control/add-to-panel.sh
   ```
   Then log out and log back in (or restart wf-panel-pi) for the change to take effect.

   **Method 2 - Manual via Config File:**
   - Edit `~/.config/wf-panel-pi.ini`
   - Find the `[panel]` section
   - Look for existing launcher entries (e.g., `launcher_000001=lxde-x-www-browser.desktop`)
   - Add a new line with the next available number: `launcher_000004=brightness-control.desktop`
   - Save the file and restart wf-panel-pi or log out/in

## Usage

### GUI Mode

**Panel Widget:**
Click the brightness control icon in your panel to open the control window.

**Manual Launch:**
```bash
~/brightness-control/brightness_control.py
```

### Command Line Mode

The application also works as a command-line tool. Run without arguments to see help:

```bash
~/brightness-control/brightness_control.py --help
```

**Examples:**

```bash
# Get current brightness
~/brightness-control/brightness_control.py get
# Output: 50% (15/31)

# Set brightness to 50%
~/brightness-control/brightness_control.py set 50

# Increase brightness by 10%
~/brightness-control/brightness_control.py +10

# Decrease brightness by 20%
~/brightness-control/brightness_control.py -20

# Turn backlight off
~/brightness-control/brightness_control.py off

# Turn backlight on
~/brightness-control/brightness_control.py on

# Set to maximum brightness
~/brightness-control/brightness_control.py max

# Set to minimum brightness (but not off)
~/brightness-control/brightness_control.py min
```

**Optional: Create a shortcut command**

You can create a symlink or alias for easier access:

```bash
# Create symlink (requires sudo)
sudo ln -s /home/pi/brightness-control/brightness_control.py /usr/local/bin/brightness

# Then use it simply as:
brightness get
brightness set 50
brightness +10
```

Or add an alias to your `~/.bashrc`:
```bash
echo 'alias brightness="~/brightness-control/brightness_control.py"' >> ~/.bashrc
source ~/.bashrc

# Then use:
brightness get
brightness set 50
```

### Control Window

The control window provides:
- **Brightness Slider**: Drag to adjust brightness (0-100%)
- **Brightness Value**: Displays current percentage and raw value (e.g., "50% (15/31)")
- **Turn off backlight**: Checkbox to completely turn off the backlight

### Double-Tap Wake

When the backlight is turned off:
- The screen will be completely dark
- Double-tap anywhere on the screen quickly (within 500ms)
- The brightness will be restored to the last set value

## Service Management

The application runs as a systemd user service and starts automatically on login.

**Start the service:**
```bash
systemctl --user start brightness-control.service
```

**Stop the service:**
```bash
systemctl --user stop brightness-control.service
```

**Check service status:**
```bash
systemctl --user status brightness-control.service
```

**Disable auto-start:**
```bash
systemctl --user disable brightness-control.service
```

## Technical Details

### Backlight Control

The widget controls the backlight via sysfs:
- Brightness: `/sys/class/backlight/10-0045/brightness` (0-31)
- Power: `/sys/class/backlight/10-0045/bl_power` (0=on, 1=off)

The backlight device path is auto-detected, so it should work even if the device ID changes.

### Double-Tap Detection

Double-tap detection monitors touch events via `/dev/input/event4` (touchscreen) using the `evdev` library. When the backlight is off, the application monitors for double-tap gestures and restores brightness.

### Permissions

The installation script:
- Adds the user to `video` and `input` groups
- Creates udev rules to allow backlight power control
- Sets up proper permissions for touchscreen access

## Troubleshooting

### Widget doesn't appear in panel

1. Make sure the desktop entry is installed:
   ```bash
   ls ~/.local/share/applications/brightness-control.desktop
   ```

2. Try refreshing the desktop database:
   ```bash
   update-desktop-database ~/.local/share/applications
   ```

3. Check that the launcher was added to the panel config:
   ```bash
   grep brightness-control ~/.config/wf-panel-pi.ini
   ```

4. Restart wf-panel-pi:
   ```bash
   pkill wf-panel-pi
   # It should auto-restart, or log out and log back in
   ```

### Cannot control brightness

1. Check if you're in the video group:
   ```bash
   groups | grep video
   ```

2. If not, log out and log back in after installation.

3. Check permissions:
   ```bash
   ls -l /sys/class/backlight/*/brightness
   ls -l /sys/class/backlight/*/bl_power
   ```

### Double-tap doesn't work

1. Check if python3-evdev is installed:
   ```bash
   python3 -c "import evdev; print('evdev available')"
   ```

2. Check if the touchscreen device is accessible:
   ```bash
   ls -l /dev/input/event4
   ```

3. Make sure you're in the input group (log out/in after adding).

### Service doesn't start

1. Check service status:
   ```bash
   systemctl --user status brightness-control.service
   ```

2. Check logs:
   ```bash
   journalctl --user -u brightness-control.service
   ```

3. Make sure DISPLAY is set correctly in the service file.

## Compatibility

- **Raspberry Pi OS Bookworm**: Fully tested and supported
- **Raspberry Pi OS Trixie**: Compatible (Debian 13)
- **Other Debian-based distributions**: May work with minor modifications

## File Structure

```
~/brightness-control/
├── brightness_control.py      # Main application
├── brightness-control.desktop  # Desktop entry for panel
├── brightness-control.service  # Systemd service file
├── install.sh                 # Installation script
└── README.md                  # This file
```

## Uninstallation

To remove the brightness control widget:

1. Stop and disable the service:
   ```bash
   systemctl --user stop brightness-control.service
   systemctl --user disable brightness-control.service
   ```

2. Remove files:
   ```bash
   rm -rf ~/brightness-control
   rm ~/.local/share/applications/brightness-control.desktop
   rm ~/.config/systemd/user/brightness-control.service
   ```

3. Remove udev rule (optional):
   ```bash
   sudo rm /etc/udev/rules.d/99-backlight-control.rules
   sudo udevadm control --reload-rules
   ```

## License

This project is provided as-is for use on Raspberry Pi systems.

## Support

For issues or questions, please check the troubleshooting section above or open an issue on Github.


