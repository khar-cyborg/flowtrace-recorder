import threading
import time
from playwright.sync_api import sync_playwright

class WebRecorder:
    def __init__(self, callback_step):
        self.callback_step = callback_step # Function to call when a step is recorded
        self.playwright = None
        self.browser = None
        self.page = None
        self.is_recording = False
        self.stop_event = threading.Event()
        self.record_thread = None

    def start(self, url):
        if self.is_recording:
            return
        self.is_recording = True
        self.stop_event.clear()
        
        # Run browser in a separate thread so it doesn't block UI
        self.record_thread = threading.Thread(target=self._run_browser, args=(url,))
        self.record_thread.start()

    def stop(self):
        if not self.is_recording:
            return
        self.is_recording = False
        self.stop_event.set()

        if self.record_thread and self.record_thread.is_alive():
            self.record_thread.join(timeout=5)

    def _run_browser(self, url):
        with sync_playwright() as p:
            self.browser = p.chromium.launch(headless=False)
            context = self.browser.new_context()
            
            # Expose binding function to Python
            context.expose_binding("py_record_step", self._handle_step)
            
            self.page = context.new_page()
            
            # Inject recording script on every page load
            self.page.add_init_script(self.get_preload_script())
            
            # Forward console logs to Python
            self.page.on("console", lambda msg: print(f"BROWSER_LOG: {msg.text}"))
            
            try:
                self.page.goto(url)
            except Exception as e:
                print(f"Error navigating: {e}")

            # Keep alive until stopped or browser closed
            while not self.stop_event.is_set():
                try:
                    if self.page.is_closed():
                        break
                    self.page.wait_for_timeout(500)
                except Exception:
                    break
            
            # Cleanup
            try:
                if self.browser:
                    self.browser.close()
            except Exception as e:
                print(f"Error closing browser: {e}")
            finally:
                self.browser = None
                self.page = None

    def _handle_step(self, source, action):
        """
        Called from JavaScript.
        action is a dict: {'type': 'click'|'type', 'selector': '...', 'description': '...', 'text': '...'}
        """
        if not self.is_recording:
            return

        # Create a text description
        if action['type'] == 'click':
            desc = f"Web Click: {action['selector']}"
        elif action['type'] == 'type':
            desc = f"Web Type: \"{action['text']}\" into {action['selector']}"
        else:
            desc = f"Web Action: {action['type']} on {action['selector']}"
            
        # We don't have a screenshot here directly unless we capture one via page.screenshot()
        # Capturing screenshot via Playwright is safer here
        try:
            png_bytes = self.page.screenshot()
        except Exception:
            png_bytes = b""
            
        # Pass to main recorder to add to list
        # We pass a dict with extra metadata
        extra_data = {
            'selector': action['selector'],
            'action_type': action['type'],
            'text': action.get('text', '')
        }
        
        self.callback_step(desc, png_bytes, extra_data)

    def get_preload_script(self):
        return """
        (() => {
            if (window._recorder_injected) return;
            window._recorder_injected = true;

            function getSelector(el) {
                // 1. ID
                if (el.id) return '#' + el.id;
                
                // 2. Data Attributes
                if (el.getAttribute('data-testid')) return `[data-testid="${el.getAttribute('data-testid')}"]`;
                
                // 3. Text Content (Buttons/Links/Labels)
                if (['BUTTON', 'A', 'LABEL', 'SPAN'].includes(el.tagName) && el.innerText.trim().length > 0 && el.innerText.trim().length < 30) {
                     const text = el.innerText.trim();
                     const tag = el.tagName.toLowerCase();
                     
                     // Check uniqueness manually cause :has-text is not valid CSS
                     const elements = Array.from(document.querySelectorAll(tag));
                     const matches = elements.filter(e => e.innerText.includes(text));
                     
                     if (matches.length === 1) {
                         return `${tag}:has-text("${text}")`;
                     }
                }
                
                // 4. Class Name
                let selector = el.tagName.toLowerCase();
                if (el.className && typeof el.className === 'string') {
                    const classes = Array.from(el.classList).join('.');
                    if (classes) {
                        selector += '.' + classes;
                    }
                }
                
                // 5. Nth-match fallback logic
                // If the current selector is not unique, find its index relative to siblings or globally
                const matches = document.querySelectorAll(selector);
                if (matches.length > 1) {
                    for (let i = 0; i < matches.length; i++) {
                        if (matches[i] === el) {
                            return `${selector} >> nth=${i}`;
                        }
                    }
                }
                
                return selector;
            }

            document.addEventListener('click', (e) => {
                try {
                console.log("Recorder: Click detected", e.target);
                const selector = getSelector(e.target);
                console.log("Recorder: Selector found", selector);
                // Highlight
                e.target.style.outline = '2px solid red';
                setTimeout(() => e.target.style.outline = '', 500);
                
                if (window.py_record_step) {
                    window.py_record_step({
                        type: 'click',
                        selector: selector,
                        description: 'Click'
                    });
                } else {
                    console.error("Recorder: window.py_record_step is missing!");
                }
                } catch (err) {
                    console.error("Recorder Error in click handler:", err);
                }
            }, true);

            // Capture 'Enter' key on inputs
            document.addEventListener('keydown', (e) => {
                try {
                if (e.key === 'Enter') {
                    console.log("Recorder: Enter key detected", e.target);
                    const selector = getSelector(e.target);
                    if (window.py_record_step) {
                        window.py_record_step({
                            type: 'press',
                            selector: selector,
                            text: 'Enter',
                            description: 'Press Enter'
                        });
                    } else {
                        console.error("Recorder: window.py_record_step is missing!");
                    }
                }
                } catch (err) {
                    console.error("Recorder Error in keydown handler:", err);
                }
            }, true);

            document.addEventListener('change', (e) => {
                try {
                console.log("Recorder: Interaction detected", e.type, e.target);
                const selector = getSelector(e.target);
                console.log("Recorder: Selector found", selector);
                
                if (window.py_record_step) {
                    window.py_record_step({
                        type: 'type',
                        selector: selector,
                        text: e.target.value,
                        description: 'Type'
                    });
                } else {
                    console.error("Recorder: window.py_record_step is missing!");
                }
                } catch (err) {
                    console.error("Recorder Error in change handler:", err);
                }
            }, true);
        })();
        """
