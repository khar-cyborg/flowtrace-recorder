import multiprocessing
import traceback
import os
import datetime
import sys
import subprocess
from playwright.__main__ import main as playwright_main
# Only import UI if not in codegen mode to save startup time/resources
if "--codegen" not in sys.argv:
    from app.ui import FlowTraceApp

def main():
    # Handle CLI args first
    if len(sys.argv) > 1:
        if sys.argv[1] == "--codegen":
            if len(sys.argv) > 2:
                url = sys.argv[2]
                sys.argv = ["playwright", "codegen", url]
                playwright_main()
            else:
                print("Usage: FlowTrace --codegen <url>")
            return

        # Handle playwright install via subprocess call (which passes -m playwright ...)
        # When running as an EXE, sys.executable is the EXE itself.
        # So subprocess.call([exe, "-m", "playwright", ...]) results in argv=['exe', '-m', 'playwright', ...]
        elif len(sys.argv) > 2 and sys.argv[1] == "-m" and sys.argv[2] == "playwright":
             # We need to strip the first 3 args: [exe, -m, playwright]
             # and prepend 'playwright' for the internal main function check if needed,
             # but actually playwright.main checks sys.argv[1] usually.
             
             # Let's reconstruct sys.argv to what playwright expects: ['playwright', 'install', 'chromium']
             # Actual sys.argv is ['path/to/exe', '-m', 'playwright', 'install', 'chromium']
             sys.argv = ["playwright"] + sys.argv[3:]
             playwright_main()
             return

    try:
        app = FlowTraceApp()
        app.mainloop()
    except Exception as e:
        # Log fatal error to Documents folder
        docs_path = os.path.join(os.path.expanduser("~"), "Documents")
        log_path = os.path.join(docs_path, "flowtrace_error.log")

        with open(log_path, "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n[{timestamp}] FATAL ERROR:\n")
            f.write(traceback.format_exc())
            f.write("\n" + "-"*50 + "\n")

        # Try to show a message box if possible
        try:
            import tkinter.messagebox
            tkinter.messagebox.showerror("Fatal Error", f"An unexpected error occurred.\nSee log at: {log_path}\n\nError: {e}")
        except Exception:
            pass



if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
