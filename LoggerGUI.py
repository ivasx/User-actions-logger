import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk, scrolledtext, messagebox, filedialog

from pynput import keyboard

from Logger import Logger


class LoggerGUI:
    def __init__(self):
        self.logger = None
        self.setup_ui()

    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("Action Logger")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')

        # Style
        style = ttk.Style()
        style.theme_use('clam')

        # Vertical panes
        control_frame = ttk.LabelFrame(self.root, text="Control Panel", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        # Buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X)

        self.start_btn = ttk.Button(btn_frame, text="▶️ Запустити", command=self.start_logging, width=15)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="⏹️ Зупинити", command=self.stop_logging,
                                   width=15, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.export_btn = ttk.Button(btn_frame, text="📊 Експорт статистики",
                                     command=self.export_stats, width=20)
        self.export_btn.pack(side=tk.LEFT, padx=5)

        self.view_log_btn = ttk.Button(btn_frame, text="📂 Відкрити лог",
                                       command=self.view_log_file, width=15)
        self.view_log_btn.pack(side=tk.LEFT, padx=5)

        # Log level
        level_frame = ttk.Frame(control_frame)
        level_frame.pack(fill=tk.X, pady=5)

        ttk.Label(level_frame, text="Log level:").pack(side=tk.LEFT, padx=5)
        self.log_level_var = tk.StringVar(value='INFO')
        log_level_combo = ttk.Combobox(level_frame, textvariable=self.log_level_var,
                                       values=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                                       width=15, state='readonly')
        log_level_combo.pack(side=tk.LEFT, padx=5)

        # Actions filters
        filter_frame = ttk.LabelFrame(self.root, text="🔍 Actions filters", padding=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        self.filter_vars = {}

        filters = [
            ('keyboard', '⌨️ Pressing keys', True),
            ('keyboard_release', '⌨️ Releasing keys', False),
            ('mouse_click', '🖱️ Mouse clicks', True),
            ('mouse_scroll', '🖱️ Scrolling', True),
            ('mouse_move', '🖱️ Mouse movement', False)
        ]

        for i, (key, label, default) in enumerate(filters):
            var = tk.BooleanVar(value=default)
            self.filter_vars[key] = var
            cb = ttk.Checkbutton(filter_frame, text=label, variable=var,
                                 command=self.update_filters)
            cb.grid(row=i // 2, column=i % 2, sticky=tk.W, padx=10, pady=2)

        # Налаштування гарячої клавіші
        hotkey_frame = ttk.LabelFrame(self.root, text="⌨️ Stop hot key", padding=10)
        hotkey_frame.pack(fill=tk.X, padx=10, pady=5)

        hotkey_inner = ttk.Frame(hotkey_frame)
        hotkey_inner.pack(fill=tk.X)

        self.hotkey_enabled_var = tk.BooleanVar(value=True)
        hotkey_cb = ttk.Checkbutton(hotkey_inner, text="Enable stop via",
                                    variable=self.hotkey_enabled_var,
                                    command=self.update_hotkey_setting)
        hotkey_cb.pack(side=tk.LEFT, padx=5)

        self.hotkey_var = tk.StringVar(value='ESC')
        hotkey_combo = ttk.Combobox(hotkey_inner, textvariable=self.hotkey_var,
                                    values=['ESC', 'F12', 'F10', 'F9', 'Pause'],
                                    width=10, state='readonly')
        hotkey_combo.pack(side=tk.LEFT, padx=5)
        hotkey_combo.bind('<<ComboboxSelected>>', lambda e: self.update_hotkey_setting())

        # Statistics
        stats_frame = ttk.LabelFrame(self.root, text="📊 Current session statistics", padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=10,
                                                    font=('Consolas', 10))
        self.stats_text.pack(fill=tk.BOTH, expand=True)

        # Останні події
        events_frame = ttk.LabelFrame(self.root, text="📝 Recent events", padding=10)
        events_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.events_text = scrolledtext.ScrolledText(events_frame, height=15,
                                                     font=('Consolas', 9))
        self.events_text.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="Ready to work.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                               relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Update statistics
        self.update_statistics()

        # Close window protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_logging(self):
        try:
            log_level = self.log_level_var.get()
            self.logger = Logger(log_level=log_level)

            # Application of filters
            for key, var in self.filter_vars.items():
                self.logger.set_filter(key, var.get())

            # Hotkey settings
            self.update_hotkey_setting()

            self.logger.start()

            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_var.set("🟢 Logging is active")

            # Start updating statistics
            self.update_statistics()
            self.update_events()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start logging:\n{e}")

    def stop_logging(self):
        if self.logger:
            self.logger.stop()

            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_var.set("🔴 Login stopped")

    def update_filters(self):
        if self.logger:
            for key, var in self.filter_vars.items():
                self.logger.set_filter(key, var.get())

    def update_hotkey_setting(self):
        if not self.logger:
            return

        # On/Off
        enabled = self.hotkey_enabled_var.get()
        self.logger.enable_hotkey_stop(enabled)

        # Select a key
        key_name = self.hotkey_var.get()
        key_map = {
            'ESC': keyboard.Key.esc,
            'F12': keyboard.Key.f12,
            'F10': keyboard.Key.f10,
            'F9': keyboard.Key.f9,
            'Pause': keyboard.Key.pause
        }

        if key_name in key_map:
            self.logger.set_stop_key(key_map[key_name])

    def update_statistics(self):
        if self.logger and self.logger.is_running:
            self.stats_text.delete(1.0, tk.END)

            stats_info = f"Start time: {self.logger.session_start.strftime('%H:%M:%S')}\n"
            stats_info += f"Duration: {datetime.now() - self.logger.session_start}\n"
            stats_info += f"Logging level: {self.logger.log_level}\n\n"
            stats_info += "EVENTS:\n"
            stats_info += "-" * 40 + "\n"

            for event_type, count in sorted(self.logger.stats.items()):
                stats_info += f"{event_type:.<30} {count:>5}\n"

            stats_info += "-" * 40 + "\n"
            stats_info += f"{'TOTAL:':.<30} {sum(self.logger.stats.values()):>5}\n"

            self.stats_text.insert(1.0, stats_info)

            # Planning for the next update
            self.root.after(1000, self.update_statistics)

    def update_events(self):
        if self.logger and self.logger.is_running:
            self.events_text.delete(1.0, tk.END)

            events = list(reversed(self.logger.recent_events[-50:]))
            self.events_text.insert(1.0, '\n'.join(events))

            self.events_text.see(1.0)

            self.root.after(500, self.update_events)

    def export_stats(self):
        if not self.logger:
            messagebox.showwarning("Warning", "First, start logging.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            self.logger.export_statistics(filename)
            messagebox.showinfo("Success", f"Statistics exported to:\n{filename}")

    def view_log_file(self):
        if self.logger and os.path.exists(self.logger.current_log_file):
            os.startfile(self.logger.current_log_file)
        else:
            messagebox.showwarning("Warning", "Log file not found")

    def on_closing(self):
        if self.logger and self.logger.is_running:
            if messagebox.askokcancel("Exit", "Stop logging and exit?"):
                self.stop_logging()
                self.root.destroy()
        else:
            self.root.destroy()

    def run(self):
        self.root.mainloop()