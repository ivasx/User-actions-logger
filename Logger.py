import json
import logging
import os
from datetime import datetime
from pynput import keyboard, mouse


class Logger:
    """
    Handles logging of user actions (keyboard and mouse) and maintains event statistics.

    This class sets up logging and provides functionality to track user input events
    such as keyboard presses/releases, mouse movements, clicks, and scrolling.
    It allows the configuration of filters to control which types of events are logged
    and includes the ability to stop logging using a hotkey. Logged sessions can be
    exported to JSON format, and runtime statistics are tracked and reported.
    """

    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    def __init__(self, log_dir='logs', log_level='INFO'):
        self.log_dir = log_dir
        self.log_level = log_level
        self.is_running = False
        self.stats = {}
        self.session_start = None

        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Logger setup
        self._setup_logger()

        # Init listeners
        self.keyboard_listener = None
        self.mouse_listener = None

        # Init filters
        self.filters = {
            'keyboard': True,
            'mouse_move': False,
            'mouse_click': True,
            'mouse_scroll': True
        }

        # Init hotkey stop listener
        self.stop_key = keyboard.Key.esc
        self.stop_on_hotkey = False

    def _setup_logger(self):
        timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        log_filename = os.path.join(self.log_dir, f'user_actions_{timestamp}.log')

        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%d-%m-%Y %H:%M:%S'
        )

        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        self.logger = logging.getLogger('UserActionLogger')
        self.logger.setLevel(self.LOG_LEVELS[self.log_level])
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.current_log_file = log_filename

        self.logger.info("=" * 70)
        self.logger.info("NEW LOG SESSION STARTED:")
        self.logger.info(f"Log level: {self.log_level}")
        self.logger.info(f"Log file: {log_filename}")
        self.logger.info("=" * 70)

    def _on_press(self, key):
        if self.stop_on_hotkey and key == self.stop_key:
            self.logger.warning(f"[STOP] Pressed {self.stop_key} - stop logging.")
            self.stop()
            return False

        if not self.filters['keyboard']:
            return

        try:
            key_name = key.char if hasattr(key, 'char') else str(key)
            self.logger.info(f"[KEYBOARD] Key pressed: {key_name}")
            self.stats['keyboard_press'] += 1
        except Exception as e:
            self.logger.error(f"[KEYBOARD] Error occurred while processing key press: {e}")

    def _on_release(self, key):
        if not self.filters['keyboard_release']:
            return

        try:
            key_name = key.char if hasattr(key, 'char') else str(key)
            self.logger.debug(f"[KEYBOARD]: Released {key_name}")
            self.stats['keyboard_release'] += 1

        except Exception as e:
            self.logger.error(f"[KEYBOARD] Error occurred while processing key release: {e}")

    def _on_move(self, x, y):
        if not self.filters['mouse_move']:
            return

        self.logger.debug(f"[MOUSE] Mouse moved to position: ({x}, {y})")
        self.stats['mouse_move'] += 1

    def _on_click(self, x, y, button, pressed):
        if not self.filters['mouse_click']:
            return

        action = "pressed" if pressed else "released"
        button_name = str(button).replace('Button.', '')
        self.logger.info(f"[MOUSE] Button {button_name} {action} at position ({x}, {y})")

        if pressed:
            self.stats[f'mouse_click_{button_name}'] += 1

    def _on_scroll(self, x, y, dx, dy):
        if not self.filters['mouse_scroll']:
            return

        direction = "up" if dy > 0 else "down"
        self.logger.info(f"[MOUSE] Mouse scrolled {direction} at position ({x}, {y})")
        self.stats['mouse_scroll'] += 1

    def start(self):
        if self.is_running:
            self.logger.warning("[WARNING] Logger is already running.")
            return

        self.is_running = True
        self.session_start = datetime.now()
        self.logger.info("[INFO] Logger started.")

        # Start listeners
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.mouse_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll
        )

        self.keyboard_listener.start()
        self.mouse_listener.start()

    def stop(self):
        if not self.is_running:
            self.logger.warning("[WARNING] Logger is not running.")
            return

        self.is_running = False

        # Stop listeners
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()

        self._log_statistics()
        self.logger.info("[INFO] Logger stopped.")
        self.logger.info("=" * 70)

    def _log_statistics(self):
        if self.session_start:
            duration = datetime.now() - self.session_start
            self.logger.info("\n" + "=" * 70)
            self.logger.info("[STATISTICS] Session statistics:")
            self.logger.info(f"Total duration: {duration}")
            self.logger.info(f"Total events: {sum(self.stats.values())}")

            for event_type, count in sorted(self.stats.items()):
                self.logger.info(f"  • {event_type}: {count}")

            self.logger.info("=" * 70)

    def set_filter(self, filter_name, enabled):
        if filter_name in self.filters:
            self.filters[filter_name] = enabled
            status = "enabled" if enabled else "disabled"
            self.logger.info(f"[FILTER] Filter '{filter_name}' set to {status}.")

    def export_statistics(self, filename=None):
        if filename is None:
            filename = os.path.join(self.log_dir, f'stats_{datetime.now().strftime("%d-%m-%Y %H:%M:%S")}.json')

        stats_data = {
            'session_start': self.session_start.isoformat() if self.session_start else None,
            'session_duration': str(datetime.now() - self.session_start) if self.session_start else None,
            'log_level': self.log_level,
            'filters': self.filters,
            'statistics': dict(self.stats)
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, indent=4, ensure_ascii=False)

        self.logger.info(f"[Export] Statistic exported to JSON: {filename}")

        return filename