# Contributing

Thank you for your interest in contributing to the Raspberry Pi Brightness Control Widget!

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test your changes on Raspberry Pi OS Bookworm or Trixie
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/brightness-control.git
cd brightness-control
```

2. Install dependencies:
```bash
sudo apt-get install python3-gi python3-evdev
```

3. Test your changes:
```bash
python3 brightness_control.py --help
python3 brightness_control.py get
```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add comments for complex logic
- Keep functions focused and small

## Testing

Please test your changes on:
- Raspberry Pi OS Bookworm (Debian 12)
- Raspberry Pi OS Trixie (Debian 13) if possible
- Official Raspberry Pi 5-inch touch screen

## Reporting Issues

If you find a bug, please open an issue with:
- Description of the problem
- Steps to reproduce
- System information (OS version, Python version)
- Any error messages

Thank you for contributing!

