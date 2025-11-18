# Setting up GitHub Repository

## Initial Setup

1. Create a new repository on GitHub (don't initialize with README, .gitignore, or license)

2. Add the remote and push:
```bash
cd ~/brightness-control
git remote add origin https://github.com/YOUR_USERNAME/brightness-control.git
git branch -M main
git commit -m "Initial commit: Raspberry Pi brightness control widget"
git push -u origin main
```

## Files Included

- `brightness_control.py` - Main application (GUI + CLI)
- `install.sh` - Installation script
- `add-to-panel.sh` - Panel integration helper
- `brightness-control.desktop` - Desktop entry file
- `brightness-control.service` - Systemd service file
- `launch-brightness-control.sh` - Wrapper script
- `README.md` - Documentation
- `LICENSE` - MIT License
- `.gitignore` - Git ignore rules

## Optional: Add GitHub Actions

You can add CI/CD later if needed, but for now the basic setup is complete.

## Release Tags

When ready to release:
```bash
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0
```
