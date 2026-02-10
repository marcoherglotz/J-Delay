# ***J-Delay.py***
# Version: ***1.0***
# Description: ***JACK Audio Input Latency Compensator***
# Author: Marco Herglotz
# License: ***GPLv3***

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import numpy as np
import argparse
import time
import configparser

try:
    import jack

    JACK_AVAILABLE = True
except ImportError:
    JACK_AVAILABLE = False

CONFIG_FILE = "J-Delay.ini"


class JDelayApp:
    def __init__(
        self,
        root,
        channels=2,
        max_delay_ms=1000,
        initial_delay=0.0,
        autostart=False,
        channel_names=None,
        loaded_delays=None,
    ):
        self.root = root
        self.root.title("J-Delay Controller by Marco Herglotz in 2026 - NoNo19-Edition")

        self.channels = channels
        if self.channels < 2:
            self.channels = 2

        self.max_delay_ms = max_delay_ms
        self.initial_delay = initial_delay
        self.autostart = autostart
        self.sample_rate = 44100
        self.channel_names = channel_names if channel_names else {}

        # Load delays if provided via config, else default
        if loaded_delays and len(loaded_delays) >= self.channels:
            self.delays_ms = loaded_delays[: self.channels]
        else:
            self.delays_ms = [initial_delay] * self.channels
            # If we loaded fewer delays than channels, fill rest with 0
            if loaded_delays:
                for i in range(len(loaded_delays)):
                    if i < self.channels:
                        self.delays_ms[i] = loaded_delays[i]

        self.buffers = []
        self.write_pointers = [0] * self.channels

        self.client = None
        self.active = False
        self.blink_job = None
        self.blink_state = False
        self.blink_color = "red"

        self.in_ports = []
        self.out_ports = []
        self.link_vars = {}
        self.edit_names_var = tk.BooleanVar(value=False)
        self.preset_buttons = []

        self.create_widgets()

        if not JACK_AVAILABLE:
            self.set_status("error", "Lib missing")
            self.activate_btn.config(state="disabled")
            messagebox.showerror("Error", "Python library 'JACK-Client' missing.")
        else:
            self.root.after(100, self.initial_connect)

    def resize_window(self):
        self.root.update_idletasks()
        content_height = self.scrollable_frame.winfo_reqheight()
        OVERHEAD = 150  # Increased for Preset Bar
        needed_height = content_height + OVERHEAD
        MAX_HEIGHT = 615
        final_height = min(needed_height, MAX_HEIGHT)
        self.root.geometry(f"650x{final_height}")
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TLabel", font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 9, "bold"))
        style.configure("Link.TCheckbutton", font=("Segoe UI", 8))
        style.configure("Preset.TButton", font=("Segoe UI", 8))

        # --- Header ---
        self.header_frame = ttk.Frame(self.root)
        self.header_frame.pack(side="top", fill="x", pady=(5, 0), padx=15)

        # Top Row: Title + Edit/Config
        top_row = ttk.Frame(self.header_frame)
        top_row.pack(fill="x")
        ttk.Label(top_row, text="J-Delay", font=("Segoe UI", 14, "bold")).pack(side="left")

        cfg_frame = ttk.Frame(top_row)
        cfg_frame.pack(side="right")
        ttk.Checkbutton(
            cfg_frame, text="Edit Names", variable=self.edit_names_var, command=self.refresh_name_cursors
        ).pack(side="left", padx=10)
        ttk.Button(cfg_frame, text="-2 Ch", width=6, command=self.remove_channels).pack(side="left", padx=2)
        ttk.Button(cfg_frame, text="+2 Ch", width=6, command=self.add_channels).pack(side="left", padx=2)

        # Bottom Row: Presets
        preset_frame = ttk.LabelFrame(self.header_frame, text="Presets (L-Click Load | R-Click Save)")
        preset_frame.pack(fill="x", pady=5)

        for i in range(1, 9):
            btn = ttk.Button(preset_frame, text=str(i), width=3, style="Preset.TButton")
            btn.pack(side="left", padx=2, pady=2, fill="x", expand=True)
            # Bindings
            btn.bind("<Button-1>", lambda e, slot=i: self.load_preset(slot))
            btn.bind("<Button-3>", lambda e, slot=i: self.save_preset(slot))
            self.preset_buttons.append(btn)

        # --- Footer ---
        self.footer_frame = ttk.Frame(self.root)
        self.footer_frame.pack(side="bottom", fill="x", pady=10, padx=15)

        self.activate_btn = ttk.Button(self.footer_frame, text="ACTIVATE", command=self.toggle_activation, width=15)
        self.activate_btn.pack(side="left")

        status_frame = ttk.Frame(self.footer_frame)
        status_frame.pack(side="right")
        self.status_led = tk.Canvas(status_frame, width=16, height=16, highlightthickness=0)
        self.status_led.pack(side="left", padx=5)
        self.led_circle = self.status_led.create_oval(2, 2, 14, 14, fill="gray", outline="")
        self.status_label = ttk.Label(status_frame, text="Init...", font=("Segoe UI", 9))
        self.status_label.pack(side="left")

        # --- Main Area ---
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(side="top", fill="both", expand=True, padx=10)

        self.canvas = tk.Canvas(self.main_container, bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=self.canvas.yview)

        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.columnconfigure(0, weight=1)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.render_channels()

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        if self.scrollable_frame.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def render_channels(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.sliders = []
        self.entries = []
        self.name_labels = []
        self.link_vars = {}

        CHECKBOX_COL_WIDTH = 55

        for i in range(self.channels):
            channel_idx = i + 1
            name = self.channel_names.get(channel_idx, f"Channel {channel_idx}")

            frame = ttk.Frame(self.scrollable_frame)
            frame.pack(fill="x", pady=2, padx=5, expand=True)

            left_col = tk.Frame(frame, width=CHECKBOX_COL_WIDTH, height=20)
            left_col.pack_propagate(False)
            left_col.pack(side="left", padx=(0, 5))

            if i % 2 == 0 and (i + 1) < self.channels:
                link_var = tk.BooleanVar(value=False)
                self.link_vars[i] = link_var
                cb = ttk.Checkbutton(left_col, text="Link", variable=link_var, style="Link.TCheckbutton")
                cb.pack(side="left", anchor="w")

            lbl = ttk.Label(frame, text=name, width=15, anchor="w")
            lbl.pack(side="left")
            lbl.bind("<Button-1>", lambda e, idx=channel_idx: self.rename_channel(idx))
            self.name_labels.append(lbl)

            val = self.delays_ms[i] if i < len(self.delays_ms) else 0.0
            entry_var = tk.StringVar(value=f"{val:.2f}")
            self.entries.append(entry_var)

            slider = ttk.Scale(
                frame,
                from_=0,
                to=self.max_delay_ms,
                orient="horizontal",
                command=lambda v, idx=i: self.update_from_slider(idx, v),
            )
            slider.pack(side="left", fill="x", expand=True, padx=(40, 5))
            slider.set(val)
            self.sliders.append(slider)

            entry = ttk.Entry(frame, textvariable=entry_var, width=7, font=("Consolas", 10))
            entry.pack(side="left")
            entry.bind("<Return>", lambda event, idx=i, var=entry_var: self.update_from_entry(idx, var))
            entry.bind("<FocusOut>", lambda event, idx=i, var=entry_var: self.update_from_entry(idx, var))

            ttk.Label(frame, text="ms").pack(side="left", padx=(2, 0))

        self.refresh_name_cursors()
        self.resize_window()

    def refresh_name_cursors(self):
        is_editing = self.edit_names_var.get()
        cursor = "hand2" if is_editing else "arrow"
        color = "blue" if is_editing else "black"
        for lbl in self.name_labels:
            lbl.config(cursor=cursor, foreground=color)

    def rename_channel(self, idx):
        if not self.edit_names_var.get():
            return
        old_name = self.channel_names.get(idx, f"Channel {idx}")
        new_name = simpledialog.askstring("Rename", f"Name for Channel {idx}:", initialvalue=old_name, parent=self.root)
        if new_name:
            self.channel_names[idx] = new_name
            self.render_channels()

    # --- PRESET SYSTEM ---
    def save_preset(self, slot):
        if messagebox.askyesno("Save Preset", f"Save current setup to Preset {slot}?"):
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            section = f"PRESET_{slot}"
            config[section] = {}
            config[section]["channels"] = str(self.channels)

            # Save Delays
            delays_str = ",".join([f"{d:.2f}" for d in self.delays_ms])
            config[section]["delays"] = delays_str

            # Save Names
            for idx, name in self.channel_names.items():
                config[section][f"name_{idx}"] = name

            with open(CONFIG_FILE, "w") as f:
                config.write(f)
            messagebox.showinfo("Saved", f"Preset {slot} saved!")

    def load_preset(self, slot):
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        section = f"PRESET_{slot}"

        if section not in config:
            messagebox.showwarning("Empty", f"Preset {slot} is empty.")
            return

        try:
            # 1. Stop Audio if structural change needed
            self.ensure_stopped()

            # 2. Load Channels
            new_channels = config.getint(section, "channels")
            self.channels = new_channels

            # 3. Load Delays
            delays_str = config.get(section, "delays")
            self.delays_ms = [float(x) for x in delays_str.split(",")]
            # Padding if mismatch
            while len(self.delays_ms) < self.channels:
                self.delays_ms.append(0.0)
            self.write_pointers = [0] * self.channels

            # 4. Load Names
            self.channel_names = {}
            for key in config[section]:
                if key.startswith("name_"):
                    idx = int(key.split("_")[1])
                    self.channel_names[idx] = config[section][key]

            self.render_channels()
            messagebox.showinfo("Loaded", f"Preset {slot} loaded.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load preset: {e}")

    def add_channels(self):
        self.ensure_stopped()
        self.channels += 2
        self.delays_ms.extend([0.0, 0.0])
        self.write_pointers.extend([0, 0])
        self.render_channels()

    def remove_channels(self):
        if self.channels <= 2:
            return
        self.ensure_stopped()
        self.channels -= 2
        self.delays_ms = self.delays_ms[: self.channels]
        self.write_pointers = self.write_pointers[: self.channels]
        self.render_channels()

    def ensure_stopped(self):
        if self.active:
            self.toggle_activation()
            # messagebox.showinfo("Info", "Audio deactivated.") # Less nagging

    def stop_blinking(self):
        if self.blink_job:
            self.root.after_cancel(self.blink_job)
            self.blink_job = None
        self.blink_state = False

    def start_blinking(self, color):
        self.stop_blinking()
        self.blink_color = color
        self._blink_loop()

    def _blink_loop(self):
        current_color = self.blink_color if self.blink_state else "#E0E0E0"
        self.status_led.itemconfig(self.led_circle, fill=current_color)
        self.blink_state = not self.blink_state
        self.blink_job = self.root.after(500, self._blink_loop)

    def set_status(self, mode, text):
        self.stop_blinking()
        self.status_label.config(text=text)
        colors = {"green": "#4CAF50", "red": "#F44336", "yellow": "#FFC107", "gray": "#9E9E9E"}
        if mode == "error":
            self.start_blinking(colors["red"])
        else:
            fill_color = colors.get(mode, "gray")
            self.status_led.itemconfig(self.led_circle, fill=fill_color)

    def initial_connect(self):
        try:
            self.client = jack.Client("j_delay", no_start_server=True)
            self.client.set_process_callback(self.process)
            self.client.set_samplerate_callback(self.samplerate_cb)
            self.sample_rate = self.client.samplerate
            self.set_status("red", "Ready")
            self.activate_btn.config(state="normal")
            if self.autostart:
                self.toggle_activation()
        except jack.JackError:
            self.set_status("error", "JACK Offline?")
            self.activate_btn.config(state="normal", command=self.retry_connect)
        except Exception as e:
            self.set_status("error", "Error")
            print(f"Init Error: {e}")

    def retry_connect(self):
        self.initial_connect()

    def toggle_activation(self):
        if not self.client:
            self.initial_connect()
            if not self.client:
                return

        if not self.active:
            try:
                self.in_ports = []
                self.out_ports = []
                for i in range(self.channels):
                    self.in_ports.append(self.client.inports.register(f"in_{i+1}"))
                    self.out_ports.append(self.client.outports.register(f"out_{i+1}"))
                self.init_buffers()
                self.client.activate()
                self.active = True
                self.activate_btn.config(text="STOP")
                self.set_status("green", "Running")
            except Exception as e:
                self.set_status("error", "Error")
                messagebox.showerror("Error", str(e))
        else:
            try:
                self.client.deactivate()
                self.active = False
                for p in self.in_ports + self.out_ports:
                    p.unregister()
                self.in_ports = []
                self.out_ports = []
                self.activate_btn.config(text="ACTIVATE")
                self.set_status("yellow", "Paused")
            except Exception as e:
                self.status_label.config(text=f"Error: {e}")

    def samplerate_cb(self, sr):
        if sr != self.sample_rate:
            self.sample_rate = sr
            self.init_buffers()

    def init_buffers(self):
        max_frames = int((self.max_delay_ms / 1000.0) * self.sample_rate) + 8192
        self.buffers = []
        self.write_pointers = [0] * self.channels
        for _ in range(self.channels):
            self.buffers.append(np.zeros(max_frames, dtype=np.float32))

    def update_from_slider(self, index, value):
        ms = float(value)
        self._apply_delay(index, ms)

    def update_from_entry(self, index, var):
        try:
            val_str = var.get().replace(",", ".")
            ms = float(val_str)
            if ms < 0:
                ms = 0
            if ms > self.max_delay_ms:
                ms = self.max_delay_ms
            self._apply_delay(index, ms)
            self.root.focus()
        except ValueError:
            var.set(f"{self.delays_ms[index]:.2f}")

    def _apply_delay(self, index, ms):
        self._set_single_channel(index, ms)
        target_idx = -1
        if index in self.link_vars:
            if self.link_vars[index].get():
                target_idx = index + 1
        elif (index - 1) in self.link_vars:
            if self.link_vars[index - 1].get():
                target_idx = index - 1
        if target_idx >= 0 and target_idx < self.channels:
            self._set_single_channel(target_idx, ms)

    def _set_single_channel(self, index, ms):
        self.delays_ms[index] = ms
        if index < len(self.sliders):
            if abs(self.sliders[index].get() - ms) > 0.01:
                self.sliders[index].set(ms)
        if index < len(self.entries):
            self.entries[index].set(f"{ms:.2f}")

    def process(self, frames):
        if not self.active:
            return
        try:
            for i in range(self.channels):
                in_data = self.in_ports[i].get_array()
                out_data = self.out_ports[i].get_array()
                buf = self.buffers[i]
                buf_len = len(buf)
                wp = self.write_pointers[i]

                if frames <= (buf_len - wp):
                    buf[wp : wp + frames] = in_data
                else:
                    part1 = buf_len - wp
                    part2 = frames - part1
                    buf[wp:buf_len] = in_data[:part1]
                    buf[0:part2] = in_data[part1:]

                delay_frames = int((self.delays_ms[i] / 1000.0) * self.sample_rate)
                rp = (wp - delay_frames) % buf_len

                if frames <= (buf_len - rp):
                    out_data[:] = buf[rp : rp + frames]
                else:
                    part1 = buf_len - rp
                    part2 = frames - part1
                    out_data[:part1] = buf[rp:buf_len]
                    out_data[part1:] = buf[0:part2]

                self.write_pointers[i] = (wp + frames) % buf_len
        except:
            pass

    def on_closing(self):
        self.save_current_state()  # Auto-Save on Close
        if self.client:
            try:
                if self.active:
                    self.client.deactivate()
                    for p in self.in_ports + self.out_ports:
                        p.unregister()
                self.client.close()
            except:
                pass
        self.root.destroy()

    def save_current_state(self):
        # Saves current state to [IO] and [LAST_SESSION]
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)  # Read existing to keep presets

        if "IO" not in config:
            config["IO"] = {}
        config["IO"]["input"] = str(self.channels)

        if "NAMES" not in config:
            config["NAMES"] = {}
        # Clear old names in NAMES section to be safe
        config["NAMES"] = {}
        for idx, name in self.channel_names.items():
            config["NAMES"][str(idx)] = name

        if "DELAYS" not in config:
            config["DELAYS"] = {}
        # Save Delays as string list or individual keys? List is cleaner.
        delays_str = ",".join([f"{d:.2f}" for d in self.delays_ms])
        config["DELAYS"]["values"] = delays_str

        try:
            with open(CONFIG_FILE, "w") as f:
                config.write(f)
        except:
            pass


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return None, {}, []
    channels = None
    names = {}
    delays = []

    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)

        if "IO" in config and "input" in config["IO"]:
            channels = config.getint("IO", "input")

        if "NAMES" in config:
            for key in config["NAMES"]:
                try:
                    names[int(key)] = config["NAMES"][key]
                except ValueError:
                    pass

        if "DELAYS" in config and "values" in config["DELAYS"]:
            try:
                delays = [float(x) for x in config["DELAYS"]["values"].split(",")]
            except:
                pass

    except:
        pass
    return channels, names, delays


if __name__ == "__main__":
    ini_channels, ini_names, ini_delays = load_config()
    default_channels = ini_channels if ini_channels else 2

    parser = argparse.ArgumentParser(description="J-Delay")
    parser.add_argument("-c", "--channels", type=int, default=default_channels)
    parser.add_argument("-d", "--delay", type=float, default=0.0)
    parser.add_argument("-m", "--max", type=float, default=1000.0)
    parser.add_argument("-a", "--autostart", action="store_true")
    args = parser.parse_args()

    root = tk.Tk()
    app = JDelayApp(
        root,
        channels=args.channels,
        max_delay_ms=args.max,
        initial_delay=args.delay,
        autostart=args.autostart,
        channel_names=ini_names,
        loaded_delays=ini_delays,
    )  # Pass loaded delays
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
