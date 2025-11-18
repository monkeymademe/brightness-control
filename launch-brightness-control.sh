#!/bin/bash
# Wrapper script to launch brightness control with proper environment

export DISPLAY=:0
export XAUTHORITY=${XAUTHORITY:-$HOME/.Xauthority}

# Ensure we're in the right directory
cd /home/pi/brightness-control

# Launch the application
exec /home/pi/brightness-control/brightness_control.py "$@"

