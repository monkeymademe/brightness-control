#!/bin/bash
#
# Installation script for Brightness Control Widget
# Raspberry Pi OS Bookworm/Trixie
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_HOME="$HOME"
SERVICE_NAME="brightness-control.service"
DESKTOP_FILE="brightness-control.desktop"

echo "Installing Brightness Control Widget..."

# Check if running as root for certain operations
if [ "$EUID" -eq 0 ]; then
    echo "Error: Please run this script as a regular user (not root)"
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
sudo apt-get update
sudo apt-get install -y python3-gi python3-evdev

# Check if user is in video and input groups
if ! groups | grep -q video; then
    echo "Adding user to video group..."
    sudo usermod -aG video "$USER"
fi

if ! groups | grep -q input; then
    echo "Adding user to input group..."
    sudo usermod -aG input "$USER"
fi

# Create udev rule for backlight control (bl_power requires root)
echo "Creating udev rules for backlight control..."
UDEV_RULE="/etc/udev/rules.d/99-backlight-control.rules"
sudo tee "$UDEV_RULE" > /dev/null <<EOF
# Allow members of video group to control backlight power
SUBSYSTEM=="backlight", ACTION=="add", RUN+="/bin/chmod 664 /sys/class/backlight/%k/bl_power"
SUBSYSTEM=="backlight", ACTION=="add", RUN+="/bin/chgrp video /sys/class/backlight/%k/bl_power"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Make the Python script executable
chmod +x "$SCRIPT_DIR/brightness_control.py"

# Create symlink for command-line access
echo "Creating command-line symlink..."
if [ ! -L /usr/local/bin/brightness ] && [ ! -f /usr/local/bin/brightness ]; then
    sudo ln -s "$SCRIPT_DIR/brightness_control.py" /usr/local/bin/brightness
    echo "  Created: /usr/local/bin/brightness"
else
    echo "  Symlink already exists or file exists at /usr/local/bin/brightness"
    echo "  Skipping symlink creation"
fi

# Install desktop entry
echo "Installing desktop entry..."
DESKTOP_DIR="$USER_HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

# Update Exec path in desktop file
sed "s|Exec=.*|Exec=$SCRIPT_DIR/brightness_control.py|" \
    "$SCRIPT_DIR/$DESKTOP_FILE" > "$DESKTOP_DIR/$DESKTOP_FILE"

chmod +x "$DESKTOP_DIR/$DESKTOP_FILE"

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

# Install systemd user service
echo "Installing systemd service..."
SYSTEMD_USER_DIR="$USER_HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"

# Update service file with correct paths
sed -e "s|%h|$USER_HOME|g" \
    -e "s|/home/pi/brightness-control|$SCRIPT_DIR|g" \
    "$SCRIPT_DIR/$SERVICE_NAME" > "$SYSTEMD_USER_DIR/$SERVICE_NAME"

# Reload systemd and enable service
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"

echo ""
echo "Installation complete!"
echo ""
echo "Command-line usage:"
echo "  brightness get              # Get current brightness"
echo "  brightness set 50           # Set brightness to 50%"
echo "  brightness +10              # Increase by 10%"
echo "  brightness -20              # Decrease by 20%"
echo "  brightness off              # Turn backlight off"
echo "  brightness on               # Turn backlight on"
echo "  brightness max              # Set to maximum"
echo "  brightness min              # Set to minimum"
echo ""
echo "GUI usage:"
echo "  brightness                  # Launch GUI (or click panel icon)"
echo ""
echo "To add the widget to your panel, run:"
echo "  $SCRIPT_DIR/add-to-panel.sh"
echo ""
echo "Or add it manually via the panel settings (see README.md for details)"
echo ""
echo "The service will start automatically on next login."
echo "To start it now, run:"
echo "  systemctl --user start brightness-control.service"
echo ""
echo "Note: You may need to log out and log back in for group changes to take effect."

