# Troubleshooting Panel Icon Not Showing

## Current Status
- ✅ Desktop entry exists in `/usr/share/applications/brightness-control.desktop`
- ✅ Desktop entry exists in `~/.local/share/applications/brightness-control.desktop`
- ✅ Desktop entry is valid (validated with desktop-file-validate)
- ✅ Config file has launcher entry: `launcher_000002=brightness-control.desktop`
- ✅ Wrapper script is executable
- ✅ App works when launched from menu
- ❌ Icon not showing in panel

## Possible Solutions

### 1. Log Out and Log Back In
wf-panel-pi may cache launcher information. Try:
- Log out completely
- Log back in
- Check if icon appears

### 2. Check Panel Config
Verify the config file:
```bash
cat ~/.config/wf-panel-pi.ini
```

Should show:
```
launcher_000002=brightness-control.desktop
```

### 3. Manual Panel Restart
```bash
pkill -9 wf-panel-pi
# Wait a few seconds, it should auto-restart
```

### 4. Verify Desktop Entry Location
```bash
ls -la /usr/share/applications/brightness-control.desktop
ls -la ~/.local/share/applications/brightness-control.desktop
```

### 5. Check Desktop Database
```bash
update-desktop-database ~/.local/share/applications/
sudo update-desktop-database /usr/share/applications/
```

### 6. Test Desktop Entry
Try launching directly:
```bash
/usr/share/applications/brightness-control.desktop
# Or
gtk-launch brightness-control.desktop
```

## Alternative: Use Menu Instead
If the panel icon doesn't work, you can always access it via:
- Applications Menu → Preferences → Brightness Control

The app functionality is working correctly, it's just the panel integration that needs troubleshooting.

