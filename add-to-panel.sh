#!/bin/bash
#
# Helper script to add Brightness Control to wf-panel-pi (Wayland panel)
# This adds a launcher button to your panel
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_HOME="$HOME"
PANEL_CONFIG="$USER_HOME/.config/wf-panel-pi.ini"
DESKTOP_FILE="brightness-control.desktop"
DESKTOP_ENTRY="$USER_HOME/.local/share/applications/$DESKTOP_FILE"

echo "Adding Brightness Control to wf-panel-pi..."

# Check if desktop entry exists
if [ ! -f "$DESKTOP_ENTRY" ]; then
    echo "Desktop entry not found. Installing it first..."
    DESKTOP_DIR="$USER_HOME/.local/share/applications"
    mkdir -p "$DESKTOP_DIR"
    sed "s|Exec=.*|Exec=$SCRIPT_DIR/brightness_control.py|" \
        "$SCRIPT_DIR/$DESKTOP_FILE" > "$DESKTOP_ENTRY"
    chmod +x "$DESKTOP_ENTRY"
fi

# Check if panel config exists
if [ ! -f "$PANEL_CONFIG" ]; then
    echo "Panel config not found. Creating default config..."
    mkdir -p "$(dirname "$PANEL_CONFIG")"
    cat > "$PANEL_CONFIG" << EOF
[panel]
widgets_left=smenu spacing4 launchers spacing8 window-list 
widgets_right=tray power ejecter updater spacing2 connect spacing2 bluetooth spacing2 netman spacing2 volumepulse spacing2 clock spacing2 batt spacing2 squeek 
EOF
fi

# Create a backup
cp "$PANEL_CONFIG" "$PANEL_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"

# Check if brightness control launcher already exists
if grep -q "brightness-control.desktop" "$PANEL_CONFIG"; then
    echo "Brightness Control launcher already exists in panel config"
    exit 0
fi

# Find the highest launcher number
max_launcher=0
while IFS='=' read -r key value; do
    if [[ $key =~ ^launcher_([0-9]+)$ ]]; then
        num=${BASH_REMATCH[1]}
        # Remove leading zeros for comparison
        num=$((10#$num))
        if [ $num -gt $max_launcher ]; then
            max_launcher=$num
        fi
    fi
done < "$PANEL_CONFIG"

# Add new launcher with next number (zero-padded to 6 digits)
next_launcher=$((max_launcher + 1))
launcher_key=$(printf "launcher_%06d" $next_launcher)

# Add the launcher to the config file
# Use Python to properly handle INI file format
python3 - "$PANEL_CONFIG" "$DESKTOP_FILE" "$launcher_key" << 'PYTHON_SCRIPT'
import configparser
import sys

config_file = sys.argv[1]
desktop_file = sys.argv[2]
launcher_key = sys.argv[3]

# Read existing config
config = configparser.ConfigParser()
config.read(config_file)

# Ensure [panel] section exists
if not config.has_section('panel'):
    config.add_section('panel')

# Add launcher
config.set('panel', launcher_key, desktop_file)

# Write back to file with launchers first
items = dict(config.items('panel'))
launchers = {k: v for k, v in items.items() if k.startswith('launcher_')}
widgets = {k: v for k, v in items.items() if not k.startswith('launcher_')}

with open(config_file, 'w') as f:
    f.write('[panel]\n')
    # Write launchers in order
    for key in sorted(launchers.keys()):
        f.write(f'{key}={launchers[key]}\n')
    # Write widgets
    for key, value in widgets.items():
        f.write(f'{key}={value}\n')
PYTHON_SCRIPT

if [ $? -eq 0 ]; then
    echo "Panel config updated successfully!"
    echo "Restarting wf-panel-pi..."
    # Try to restart the panel
    pkill -HUP wf-panel-pi 2>/dev/null || pkill wf-panel-pi 2>/dev/null || echo "Please restart wf-panel-pi manually or log out and back in"
    echo ""
    echo "Brightness Control has been added to your panel!"
    echo "You should see a brightness control icon in your panel now."
    echo ""
    echo "If the icon doesn't appear, you may need to log out and log back in."
else
    echo "Error: Failed to update panel config"
    echo ""
    echo "You can add it manually by editing: $PANEL_CONFIG"
    echo "Add a line like: launcher_000004=brightness-control.desktop"
    echo "(Use the next available launcher number)"
    exit 1
fi
