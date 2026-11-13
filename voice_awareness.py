"""
VOICE AWARENESS — Windows desktop app
Monitors microphone speech activity. If no speech is detected for the chosen
interval, the supplied alarm tone repeats until speech is detected.
"""
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

import sounddevice as sd
import webrtcvad
import pygame

APP_DIR = Path(__file__).resolve().parent
ALARM_FILE = APP_DIR / "assets" / "852Hz_alarm.mp3"
SAMPLE_RATE = 16000
FRAME_MS = 30
FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_MS / 1000)

class VoiceMonitor:
    def __init__(self, on_status):
        self.on_status = on_status
        self.vad = webrtcvad.Vad(2)  # moderate sensitivity; filters much background noise
        self.running = False
        self.stream = None
        self.thread = None
        self.interval = 30.0
        self.last_speech = time.monotonic()
        self.alarming = False
        self.lock = threading.Lock()
        self.audio_ready = False

    def _status(self, message):
        try:
            self.on_status(message)
        except Exception:
            pass

    def _audio_callback(self, indata, frames, time_info, status):
        if not self.running:
            return
        try:
            pcm = indata[:, 0].copy().tobytes()
            speech = self.vad.is_speech(pcm, SAMPLE_RATE)
            if speech:
                with self.lock:
                    self.last_speech = time.monotonic()
                    was_alarming = self.alarming
                    self.alarming = False
                if was_alarming:
                    self._stop_alarm()
                    self._status("Human speech detected — alarm stopped")
        except Exception:
            # Ignore a malformed audio frame rather than crashing the audio callback.
            pass

    def _start_alarm(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.load(str(ALARM_FILE))
                pygame.mixer.music.play(-1)
            with self.lock:
                self.alarming = True
            self._status("No speech detected — 852 Hz reminder is repeating")
        except Exception as exc:
            self._status(f"Alarm playback error: {exc}")

    def _stop_alarm(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass

    def _watch_loop(self):
        while self.running:
            with self.lock:
                elapsed = time.monotonic() - self.last_speech
                alarming = self.alarming
            if elapsed >= self.interval and not alarming:
                self._start_alarm()
            time.sleep(0.12)

    def start(self, interval_seconds):
        if self.running:
            self.set_interval(interval_seconds)
            return
        if not ALARM_FILE.exists():
            raise FileNotFoundError(f"Alarm file not found: {ALARM_FILE}")
        self.interval = float(interval_seconds)
        self.last_speech = time.monotonic()
        self.running = True
        try:
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
                blocksize=FRAME_SAMPLES,
                callback=self._audio_callback,
            )
            self.stream.start()
        except Exception:
            self.running = False
            self.stream = None
            raise
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        self._status("Microphone monitoring is ON — listening for human speech")

    def set_interval(self, seconds):
        self.interval = float(seconds)
        # Changing the interval starts a fresh quiet-time window.
        with self.lock:
            self.last_speech = time.monotonic()
            was_alarming = self.alarming
            self.alarming = False
        if was_alarming:
            self._stop_alarm()
        self._status(f"Interval updated to {self.interval:g} seconds")

    def stop(self):
        self.running = False
        self._stop_alarm()
        with self.lock:
            self.alarming = False
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        self._status("Monitoring is OFF")

class VoiceAwarenessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Awareness")
        self.root.geometry("440x540")
        self.root.minsize(400, 500)
        self.root.configure(bg="#101713")
        self.monitor = VoiceMonitor(self.set_status)
        self.interval_value = tk.StringVar(value="30")
        self.unit_value = tk.StringVar(value="Seconds")
        self.status_value = tk.StringVar(value="Monitoring is OFF")
        self.is_running = False
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground="#1c2921", background="#1c2921",
                        foreground="#e8f2eb", arrowcolor="#7ee29b")
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=9)
        style.configure("Green.TButton", background="#43c878", foreground="#07130b")
        style.map("Green.TButton", background=[("active", "#61df91")])
        style.configure("Stop.TButton", background="#26352c", foreground="#e8f2eb")

        outer = tk.Frame(self.root, bg="#101713", padx=25, pady=22)
        outer.pack(fill="both", expand=True)

        tk.Label(outer, text="VOICE AWARENESS", bg="#101713", fg="#f0f7f2",
                 font=("Segoe UI", 19, "bold")).pack(anchor="w")
        tk.Label(outer, text="Speech-aware focus reminder", bg="#101713", fg="#9bb2a2",
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 18))

        panel = tk.Frame(outer, bg="#18241c", padx=17, pady=16,
                         highlightthickness=1, highlightbackground="#2b4031")
        panel.pack(fill="x")
        tk.Label(panel, text="ALARM TONE", bg="#18241c", fg="#9bb2a2",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(panel, text="852 Hz", bg="#18241c", fg="#72e69a",
                 font=("Segoe UI", 28, "bold")).pack(anchor="w")
        tk.Label(panel, text="Your supplied MP3 • repeats until speech is detected",
                 bg="#18241c", fg="#c3d2c8", font=("Segoe UI", 9)).pack(anchor="w")

        tk.Label(outer, text="REMINDER INTERVAL", bg="#101713", fg="#dce9e0",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(22, 8))
        presets = tk.Frame(outer, bg="#101713")
        presets.pack(fill="x")
        for val in (10, 20, 30, 40, 50, 60):
            b = tk.Button(presets, text=f"{val}s", command=lambda v=val: self.choose(v, "Seconds"),
                           bg="#1c2921", fg="#e5f1e8", activebackground="#2c4935",
                           activeforeground="white", relief="flat", font=("Segoe UI", 10, "bold"),
                           padx=11, pady=9, cursor="hand2")
            b.pack(side="left", expand=True, fill="x", padx=(0 if val == 10 else 4, 0))

        custom = tk.Frame(outer, bg="#101713")
        custom.pack(fill="x", pady=(12, 0))
        tk.Label(custom, text="Custom:", bg="#101713", fg="#c3d2c8",
                 font=("Segoe UI", 10)).pack(side="left")
        self.custom_entry = ttk.Entry(custom, textvariable=self.interval_value, width=9,
                                      font=("Segoe UI", 11))
        self.custom_entry.pack(side="left", padx=(9, 7), ipady=4)
        self.unit_box = ttk.Combobox(custom, textvariable=self.unit_value,
                                     values=("Seconds", "Minutes"), state="readonly", width=10)
        self.unit_box.pack(side="left", ipady=3)
        ttk.Button(custom, text="Apply", command=self.apply_interval).pack(side="right")

        tk.Label(outer, text="STATUS", bg="#101713", fg="#dce9e0",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(23, 7))
        status_panel = tk.Frame(outer, bg="#18241c", padx=12, pady=13)
        status_panel.pack(fill="x")
        self.status_label = tk.Label(status_panel, textvariable=self.status_value,
                                     bg="#18241c", fg="#b8cbbd", wraplength=345,
                                     justify="left", font=("Segoe UI", 9))
        self.status_label.pack(anchor="w")

        controls = tk.Frame(outer, bg="#101713")
        controls.pack(fill="x", pady=(18, 0))
        self.start_button = ttk.Button(controls, text="▶  START MONITORING",
                                       style="Green.TButton", command=self.start)
        self.start_button.pack(fill="x")
        self.stop_button = ttk.Button(controls, text="■  STOP",
                                      style="Stop.TButton", command=self.stop, state="disabled")
        self.stop_button.pack(fill="x", pady=(8, 0))

        tk.Label(outer, text="Minimize the window to keep monitoring in the background.\n"
                 "Keep your microphone connected and allow Windows microphone access.",
                 bg="#101713", fg="#81968a", justify="left",
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(17, 0))

    def choose(self, value, unit):
        self.interval_value.set(str(value))
        self.unit_value.set(unit)
        self.apply_interval()

    def get_seconds(self):
        try:
            value = float(self.interval_value.get().strip())
            if value <= 0 or value > 86400:
                raise ValueError
            return value * (60 if self.unit_value.get() == "Minutes" else 1)
        except ValueError:
            raise ValueError("Enter a number greater than 0 (maximum 1440 minutes).")

    def apply_interval(self):
        try:
            seconds = self.get_seconds()
            if self.is_running:
                self.monitor.set_interval(seconds)
            else:
                self.set_status(f"Interval set to {seconds:g} seconds")
        except ValueError as exc:
            messagebox.showerror("Invalid interval", str(exc))

    def start(self):
        try:
            seconds = self.get_seconds()
            self.monitor.start(seconds)
            self.is_running = True
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
        except Exception as exc:
            self.is_running = False
            messagebox.showerror(
                "Could not start microphone",
                f"{exc}\n\nCheck Windows Settings → Privacy & security → Microphone, "
                "and make sure a microphone is connected."
            )

    def stop(self):
        self.monitor.stop()
        self.is_running = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

    def set_status(self, message):
        self.root.after(0, lambda: self.status_value.set(message))

    def on_close(self):
        if self.is_running:
            answer = messagebox.askyesno("Exit Voice Awareness",
                                         "Stop monitoring and exit?")
            if not answer:
                self.root.iconify()
                return
        self.monitor.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceAwarenessApp(root)
    root.mainloop()
