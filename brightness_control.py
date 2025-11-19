#!/usr/bin/env python3
"""
Raspberry Pi Backlight Control Widget
Controls brightness of the official 5-inch touch screen with double-tap wake functionality.
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import os
import sys
import threading
import time
import glob
from pathlib import Path

try:
    from evdev import InputDevice, categorize, ecodes
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False
    print("Warning: python3-evdev not installed. Double-tap detection will be disabled.")


class BacklightController:
    """Handles backlight brightness control via sysfs."""
    
    def __init__(self):
        self.backlight_path = self._find_backlight()
        if not self.backlight_path:
            raise RuntimeError("Could not find backlight device")
        
        self.brightness_file = os.path.join(self.backlight_path, 'brightness')
        self.max_brightness_file = os.path.join(self.backlight_path, 'max_brightness')
        self.bl_power_file = os.path.join(self.backlight_path, 'bl_power')
        
        self.max_brightness = self._read_int(self.max_brightness_file)
        self.last_brightness = self.get_brightness()
    
    def _find_backlight(self):
        """Find the backlight device path."""
        backlight_dirs = glob.glob('/sys/class/backlight/*')
        if backlight_dirs:
            return backlight_dirs[0]
        return None
    
    def _read_int(self, filepath):
        """Read an integer value from a file."""
        try:
            with open(filepath, 'r') as f:
                return int(f.read().strip())
        except (IOError, ValueError):
            return 0
    
    def _write_int(self, filepath, value):
        """Write an integer value to a file."""
        try:
            with open(filepath, 'w') as f:
                f.write(str(int(value)))
            return True
        except IOError:
            return False
    
    def get_brightness(self):
        """Get current brightness value (0-max_brightness)."""
        return self._read_int(self.brightness_file)
    
    def get_brightness_percent(self):
        """Get current brightness as percentage (0-100)."""
        if self.max_brightness == 0:
            return 0
        return int((self.get_brightness() / self.max_brightness) * 100)
    
    def set_brightness(self, value):
        """Set brightness value (0-max_brightness)."""
        value = max(0, min(value, self.max_brightness))
        if self._write_int(self.brightness_file, value):
            self.last_brightness = value
            return True
        return False
    
    def set_brightness_percent(self, percent):
        """Set brightness as percentage (0-100)."""
        value = int((percent / 100.0) * self.max_brightness)
        return self.set_brightness(value)
    
    def is_backlight_off(self):
        """Check if backlight is turned off."""
        return self._read_int(self.bl_power_file) == 1
    
    def turn_backlight_off(self):
        """Turn backlight off."""
        return self._write_int(self.bl_power_file, 1)
    
    def turn_backlight_on(self):
        """Turn backlight on."""
        return self._write_int(self.bl_power_file, 0)
    
    def restore_brightness(self):
        """Restore brightness to last set value and turn on."""
        self.set_brightness(self.last_brightness)
        self.turn_backlight_on()


class DoubleTapDetector:
    """Detects double-tap gestures on touchscreen when backlight is off."""
    
    def __init__(self, backlight_controller, callback):
        self.backlight_controller = backlight_controller
        self.callback = callback
        self.running = False
        self.thread = None
        self.touch_device = self._find_touch_device()
        
        # Double-tap detection state
        self.last_tap_time = 0
        self.tap_timeout = 0.5  # 500ms window for double-tap
        self.touch_down = False
    
    def _find_touch_device(self):
        """Find the touchscreen input device."""
        if not EVDEV_AVAILABLE:
            return None
        
        try:
            # Look for touchscreen devices
            devices = [InputDevice(path) for path in glob.glob('/dev/input/event*')]
            for device in devices:
                if 'touch' in device.name.lower() or 'TouchScreen' in device.name:
                    return device.path
        except Exception as e:
            print(f"Error finding touch device: {e}")
        
        return None
    
    def start(self):
        """Start the double-tap detection thread."""
        if not EVDEV_AVAILABLE or not self.touch_device:
            print("Double-tap detection not available")
            return
        
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_touch, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the double-tap detection thread."""
        self.running = False
    
    def _monitor_touch(self):
        """Monitor touch events in background thread."""
        try:
            device = InputDevice(self.touch_device)
            for event in device.read_loop():
                if not self.running:
                    break
                
                # Only monitor when backlight is off
                if not self.backlight_controller.is_backlight_off():
                    self.last_tap_time = 0
                    self.touch_down = False
                    continue
                
                # Detect touch events
                if event.type == ecodes.EV_KEY:
                    if event.code == ecodes.BTN_TOUCH:
                        current_time = time.time()
                        
                        if event.value == 1:  # Touch down
                            self.touch_down = True
                            # Check for double-tap
                            if current_time - self.last_tap_time < self.tap_timeout:
                                # Double-tap detected!
                                GLib.idle_add(self.callback)
                                self.last_tap_time = 0
                            else:
                                self.last_tap_time = current_time
                        
                        elif event.value == 0:  # Touch up
                            self.touch_down = False
                
        except Exception as e:
            print(f"Error monitoring touch: {e}")


class BrightnessControlWindow(Gtk.Window):
    """Main GUI window for brightness control."""
    
    def __init__(self, backlight_controller, double_tap_detector, app):
        super().__init__(title="Brightness Control")
        self.backlight_controller = backlight_controller
        self.double_tap_detector = double_tap_detector
        self.app = app  # Reference to parent app
        self.updating = False
        
        self.set_default_size(300, 200)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)
        self.add(vbox)
        
        # Brightness slider
        slider_label = Gtk.Label(label="Brightness")
        slider_label.set_halign(Gtk.Align.START)
        vbox.pack_start(slider_label, False, False, 0)
        
        self.slider = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 1
        )
        self.slider.set_value(self.backlight_controller.get_brightness_percent())
        self.slider.connect("value-changed", self.on_slider_changed)
        vbox.pack_start(self.slider, False, False, 0)
        
        # Brightness value display
        self.value_label = Gtk.Label()
        self.value_label.set_halign(Gtk.Align.CENTER)
        self.update_value_label()
        vbox.pack_start(self.value_label, False, False, 0)
        
        # Turn off backlight checkbox
        self.off_checkbox = Gtk.CheckButton(label="Turn off backlight")
        self.off_checkbox.connect("toggled", self.on_checkbox_toggled)
        vbox.pack_start(self.off_checkbox, False, False, 10)
        
        # Close button
        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", self.on_close_button_clicked)
        vbox.pack_start(close_button, False, False, 0)
        
        # Update brightness display periodically
        GLib.timeout_add(500, self.update_display)
    
    def on_slider_changed(self, widget):
        """Handle slider value change."""
        if self.updating:
            return
        
        value = int(self.slider.get_value())
        self.backlight_controller.set_brightness_percent(value)
        
        # If backlight was off, turn it on
        if self.backlight_controller.is_backlight_off():
            self.backlight_controller.turn_backlight_on()
            self.off_checkbox.set_active(False)
        
        self.update_value_label()
    
    def on_checkbox_toggled(self, widget):
        """Handle checkbox toggle."""
        if self.updating:
            return
        
        if widget.get_active():
            self.backlight_controller.turn_backlight_off()
        else:
            self.backlight_controller.turn_backlight_on()
    
    def update_value_label(self):
        """Update the brightness value label."""
        percent = self.backlight_controller.get_brightness_percent()
        raw_value = self.backlight_controller.get_brightness()
        max_value = self.backlight_controller.max_brightness
        self.value_label.set_text(f"{percent}% ({raw_value}/{max_value})")
    
    def update_display(self):
        """Periodically update the display."""
        if not self.updating:
            self.updating = True
            percent = self.backlight_controller.get_brightness_percent()
            self.slider.set_value(percent)
            self.update_value_label()
            
            # Update checkbox state
            is_off = self.backlight_controller.is_backlight_off()
            self.off_checkbox.set_active(is_off)
            self.updating = False
        
        return True
    
    def on_close_button_clicked(self, widget):
        """Handle close button click."""
        if self.app and self.app.is_service:
            # If running as service, just hide the window
            self.hide()
        else:
            # If standalone instance, quit the application
            Gtk.main_quit()
    
    def on_double_tap(self):
        """Handle double-tap wake event."""
        self.backlight_controller.restore_brightness()
        self.update_display()
        return False


class BrightnessControlApp:
    """Main application class."""
    
    def __init__(self, is_service=False):
        self.backlight_controller = None
        self.double_tap_detector = None
        self.window = None
        self.status_icon = None
        self.is_service = is_service  # Track if running as service
        
        try:
            self.backlight_controller = BacklightController()
        except RuntimeError as e:
            self._show_error(str(e))
            sys.exit(1)
        
        # Create double-tap detector
        self.double_tap_detector = DoubleTapDetector(
            self.backlight_controller,
            self.on_double_tap
        )
        
        # Create main window
        self.window = BrightnessControlWindow(
            self.backlight_controller,
            self.double_tap_detector,
            self
        )
        self.window.connect("delete-event", self.on_window_delete)
        
        # Create status icon
        self.create_status_icon()
        
        # Start double-tap detection
        self.double_tap_detector.start()
    
    def create_status_icon(self):
        """Create system tray status icon."""
        try:
            # Try to use StatusIcon (deprecated but may work)
            if hasattr(Gtk, 'StatusIcon'):
                self.status_icon = Gtk.StatusIcon()
                # Try to use a light/bulb icon
                icon_theme = Gtk.IconTheme.get_default()
                icon_names = ['lightbulb', 'lightbulb-symbolic', 'preferences-desktop-display-brightness', 
                             'display-brightness', 'gtk-info']
                
                icon_found = False
                for icon_name in icon_names:
                    if icon_theme.has_icon(icon_name):
                        self.status_icon.set_from_icon_name(icon_name)
                        icon_found = True
                        break
                
                if not icon_found:
                    # Use a default icon
                    self.status_icon.set_from_stock(Gtk.STOCK_INFO)
                
                self.status_icon.set_tooltip_text("Brightness Control")
                self.status_icon.connect("activate", self.on_status_icon_clicked)
                self.status_icon.set_visible(True)
        except Exception as e:
            print(f"Could not create status icon: {e}")
    
    def on_status_icon_clicked(self, widget):
        """Handle status icon click."""
        if self.window.get_visible():
            self.window.hide()
        else:
            self.window.show_all()
            self.window.present()
            # Bring window to front
            self.window.set_keep_above(True)
            GLib.timeout_add(100, lambda: self.window.set_keep_above(False))
    
    def on_window_delete(self, widget, event):
        """Handle window close event."""
        if self.is_service:
            # If running as service, just hide the window
            widget.hide()
            return True  # Prevent window destruction
        else:
            # If standalone instance, quit the application
            Gtk.main_quit()
            return False  # Allow window destruction
    
    def on_double_tap(self):
        """Handle double-tap wake event."""
        if self.window:
            self.window.on_double_tap()
        return False
    
    def _show_error(self, message):
        """Show error dialog."""
        dialog = Gtk.MessageDialog(
            parent=None,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            message_format=message
        )
        dialog.run()
        dialog.destroy()
    
    def run(self, show_window=False):
        """Run the application.
        
        Args:
            show_window: If True, show the window on startup. If False, start hidden.
        """
        if show_window:
            # Show window when launched from desktop/panel
            # Realize the window first to ensure it's ready
            if not self.window.get_realized():
                self.window.realize()
            self.window.show_all()
            self.window.present()
            # Force window to front and ensure it's visible
            self.window.set_keep_above(True)
            GLib.timeout_add(300, lambda: self.window.set_keep_above(False))
            # Ensure window is actually visible
            GLib.timeout_add(100, lambda: self.window.show_all() or True)
        else:
            # Start hidden - window will only show when status icon is clicked
            self.window.hide()
        Gtk.main()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Control Raspberry Pi touchscreen backlight brightness',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Launch GUI
  %(prog)s get                # Get current brightness percentage
  %(prog)s set 50             # Set brightness to 50%%
  %(prog)s +10                # Increase brightness by 10%%
  %(prog)s -20                # Decrease brightness by 20%%
  %(prog)s off                # Turn backlight off
  %(prog)s on                 # Turn backlight on
  %(prog)s max                # Set to maximum brightness
  %(prog)s min                # Set to minimum brightness (but not off)
        """
    )
    
    parser.add_argument(
        'action',
        nargs='?',
        help='Action to perform: get, set <value>, +<value>, -<value>, on, off, max, min (default: launch GUI)'
    )
    parser.add_argument(
        'value',
        nargs='?',
        type=float,
        help='Brightness value (0-100) when using "set" action'
    )
    parser.add_argument(
        '--service',
        action='store_true',
        help='Run as background service (hide GUI on startup)'
    )
    
    args = parser.parse_args()
    
    # If no arguments, launch GUI
    if args.action is None:
        # Check if service is already running
        if not args.service:
            import subprocess
            try:
                # Check if service is active
                result = subprocess.run(
                    ['systemctl', '--user', 'is-active', 'brightness-control.service'],
                    capture_output=True,
                    timeout=1
                )
                if result.returncode == 0:
                    # Service is running, try to show its window via dbus or just launch new instance
                    # For now, we'll launch a new instance that shows the window
                    pass
            except Exception:
                pass
        
        app = BrightnessControlApp(is_service=args.service)
        # If --service flag is set, start hidden (for systemd service)
        # Otherwise, show window (for desktop/panel launch)
        show_on_start = not args.service
        app.run(show_window=show_on_start)
        return
    
    # Otherwise, use CLI mode
    try:
        controller = BacklightController()
        action = args.action.lower()
        
        if action == 'get':
            # Get current brightness
            percent = controller.get_brightness_percent()
            raw = controller.get_brightness()
            max_val = controller.max_brightness
            is_off = controller.is_backlight_off()
            status = " (OFF)" if is_off else ""
            print(f"{percent}% ({raw}/{max_val}){status}")
            
        elif action == 'set':
            # Set brightness
            if args.value is None:
                print("Error: 'set' requires a value (0-100)", file=sys.stderr)
                sys.exit(1)
            value = max(0, min(100, args.value))
            if controller.set_brightness_percent(value):
                controller.turn_backlight_on()  # Ensure backlight is on
                print(f"Brightness set to {value}%")
            else:
                print("Error: Failed to set brightness", file=sys.stderr)
                sys.exit(1)
                
        elif action.startswith('+'):
            # Increase brightness
            try:
                delta = float(action[1:])
                current = controller.get_brightness_percent()
                new_value = min(100, current + delta)
                if controller.set_brightness_percent(new_value):
                    controller.turn_backlight_on()
                    print(f"Brightness increased to {new_value}%")
                else:
                    print("Error: Failed to set brightness", file=sys.stderr)
                    sys.exit(1)
            except ValueError:
                print(f"Error: Invalid increment value: {action[1:]}", file=sys.stderr)
                sys.exit(1)
                
        elif action.startswith('-'):
            # Decrease brightness
            try:
                delta = float(action[1:])
                current = controller.get_brightness_percent()
                new_value = max(0, current - delta)
                if controller.set_brightness_percent(new_value):
                    controller.turn_backlight_on()
                    print(f"Brightness decreased to {new_value}%")
                else:
                    print("Error: Failed to set brightness", file=sys.stderr)
                    sys.exit(1)
            except ValueError:
                print(f"Error: Invalid decrement value: {action[1:]}", file=sys.stderr)
                sys.exit(1)
                
        elif action == 'off':
            # Turn backlight off
            if controller.turn_backlight_off():
                print("Backlight turned off")
                # Ensure the service is running for double-tap detection
                import subprocess
                try:
                    # Always try to ensure service is running
                    result = subprocess.run(
                        ['systemctl', '--user', 'is-active', 'brightness-control.service'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode != 0:
                        # Service not active, start it
                        print("Starting background service for double-tap wake...")
                        start_result = subprocess.run(
                            ['systemctl', '--user', 'start', 'brightness-control.service'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if start_result.returncode == 0:
                            print("Service started. Double-tap the screen to wake it.")
                        else:
                            # Fallback: check if any process is running
                            pgrep_result = subprocess.run(
                                ['pgrep', '-f', 'brightness_control.py'],
                                capture_output=True,
                                timeout=2
                            )
                            if pgrep_result.returncode == 0:
                                print("Note: A brightness-control process is running. Double-tap should work.")
                            else:
                                print("Warning: Could not start service. Double-tap wake may not work.")
                                print("         Start manually with: systemctl --user start brightness-control.service")
                    else:
                        print("Double-tap detection is active. Double-tap the screen to wake it.")
                except Exception as e:
                    # If we can't check/start service, at least warn user
                    print("Note: For double-tap wake to work, ensure the brightness-control service is running.")
                    print("      Start it with: systemctl --user start brightness-control.service")
            else:
                print("Error: Failed to turn backlight off", file=sys.stderr)
                sys.exit(1)
                
        elif action == 'on':
            # Turn backlight on
            if controller.turn_backlight_on():
                print("Backlight turned on")
            else:
                print("Error: Failed to turn backlight on", file=sys.stderr)
                sys.exit(1)
                
        elif action == 'max':
            # Set to maximum
            if controller.set_brightness_percent(100):
                controller.turn_backlight_on()
                print("Brightness set to maximum (100%)")
            else:
                print("Error: Failed to set brightness", file=sys.stderr)
                sys.exit(1)
                
        elif action == 'min':
            # Set to minimum (but not off)
            if controller.set_brightness_percent(1):
                controller.turn_backlight_on()
                print("Brightness set to minimum (1%)")
            else:
                print("Error: Failed to set brightness", file=sys.stderr)
                sys.exit(1)
                
        else:
            print(f"Error: Unknown action '{action}'", file=sys.stderr)
            parser.print_help()
            sys.exit(1)
            
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


