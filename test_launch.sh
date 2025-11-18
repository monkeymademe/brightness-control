#!/bin/bash
export DISPLAY=:0
export XAUTHORITY=${XAUTHORITY:-$HOME/.Xauthority}
cd /home/pi/brightness-control
python3 brightness_control.py 2>&1
