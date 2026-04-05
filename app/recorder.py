import datetime
import threading
import time as _time
from pynput import mouse, keyboard
import mss
import mss.tools
from app.utils import get_active_window_title
from app.web_recorder import WebRecorder

class Step:
    def __init__(self, description, image_bytes, timestamp, window_title, selector=None, action_type=None, text=None):
        self.description = description
        self.image_bytes = image_bytes
        self.timestamp = timestamp
        self.window_title = window_title
        self.selector = selector
        self.action_type = action_type
        self.text = text

class Recorder:
    def __init__(self):
        self.steps = []
        self.is_recording = False
        self.mouse_listener = None
        self.keyboard_listener = None
        self.lock = threading.RLock()
        self.text_buffer = ""
        self.capture_delay = 0.3  # seconds between auto-captures
        self._last_capture_time = 0

        self.mode = "desktop" # or "web"
        self.recording_start_time = None
        self.web_recorder = WebRecorder(self.on_web_step)

    def start(self, auto_capture=True, mode="desktop", url=""):
        if self.is_recording:
            return

        self.is_recording = True
        self.mode = mode
        self.auto_capture = auto_capture
        self.steps = []
        self.text_buffer = ""
        self._last_capture_time = 0
        self.recording_start_time = _time.time()
        
        if self.mode == "web":
            self.web_recorder.start(url)
        else:
            # Start desktop listeners
            self.mouse_listener = mouse.Listener(on_click=self.on_click)
            self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
            
            self.mouse_listener.start()
            self.keyboard_listener.start()

    def get_elapsed_time(self):
        if self.recording_start_time and self.is_recording:
            elapsed = _time.time() - self.recording_start_time
            mins, secs = divmod(int(elapsed), 60)
            hrs, mins = divmod(mins, 60)
            if hrs:
                return f"{hrs}:{mins:02d}:{secs:02d}"
            return f"{mins:02d}:{secs:02d}"
        return "00:00"

    def stop(self):
        if not self.is_recording:
            return

        # Flush any remaining text
        self.flush_text()

        self.is_recording = False
        self.recording_start_time = None
        
        if self.mode == "web":
            self.web_recorder.stop()
        else:
            if self.mouse_listener:
                self.mouse_listener.stop()
            if self.keyboard_listener:
                self.keyboard_listener.stop()

    def flush_text(self):
        with self.lock:
            if self.text_buffer:
                self.capture_step(f"Typed: \"{self.text_buffer}\"")
                self.text_buffer = ""

    def capture_step(self, description):
        if not self.is_recording:
            return

        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            window_title = get_active_window_title()
            
            # Capture full screen
            with mss.mss() as sct:
                monitor = sct.monitors[1] # Primary monitor
                sct_img = sct.grab(monitor)
                img_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)

            step = Step(description, img_bytes, timestamp, window_title)

            with self.lock:
                self.steps.append(step)
                print(f"Captured: {description}")
        except Exception as e:
            print(f"Failed to capture step: {e}")

    def on_web_step(self, description, image_bytes, extra_data):
        # Callback from WebRecorder
        if not self.is_recording:
            return
            
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        window_title = "Browser" # Placeholder
        
        step = Step(description, image_bytes, timestamp, window_title, 
                    selector=extra_data.get('selector'),
                    action_type=extra_data.get('action_type'),
                    text=extra_data.get('text'))
        
        with self.lock:
            self.steps.append(step)
            print(f"Web Captured: {description}")

    def on_click(self, x, y, button, pressed):
        if pressed and self.is_recording and self.auto_capture:
            now = _time.time()
            if now - self._last_capture_time < self.capture_delay:
                return
            self._last_capture_time = now
            self.flush_text()
            self.capture_step(f"Mouse Click ({button.name}) at ({x}, {y})")

    def on_press(self, key):
        if not self.is_recording or not self.auto_capture:
            return

        try:
            if hasattr(key, 'char') and key.char:
                 # Append to buffer
                 with self.lock:
                     self.text_buffer += key.char
            else:
                self.flush_text()
                if key in [keyboard.Key.enter, keyboard.Key.tab, keyboard.Key.esc]:
                    self.capture_step(f"Key Press: {key.name}")
        except AttributeError:
            pass

    def manual_capture(self):
        self.flush_text()
        self.capture_step("Manual Capture")

    def get_steps(self):
        with self.lock:
            return list(self.steps)

    def clear(self):
        with self.lock:
            self.steps = []
            self.text_buffer = ""

    def delete_step(self, index):
        with self.lock:
            if 0 <= index < len(self.steps):
                del self.steps[index]

    def update_step(self, index, description):
        with self.lock:
            if 0 <= index < len(self.steps):
                self.steps[index].description = description

    def move_step(self, index, direction):
        with self.lock:
            target = index + direction
            if 0 <= index < len(self.steps) and 0 <= target < len(self.steps):
                self.steps[index], self.steps[target] = self.steps[target], self.steps[index]
                return True
            return False

    def add_note(self, text):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        window_title = get_active_window_title()
        step = Step(f"Note: {text}", image_bytes=b"", timestamp=timestamp, window_title=window_title)
        with self.lock:
            self.steps.append(step)
