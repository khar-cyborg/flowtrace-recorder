import platform

def get_active_window_title():
    """
    Returns the title of the currently active window.
    Returns 'Unknown Window' if it fails or if the OS is not supported.
    """
    try:
        if platform.system() == "Windows":
            import win32gui
            window = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(window)
        else:
            return "Unknown Window (Non-Windows OS)"
    except Exception as e:
        print(f"Error getting window title: {e}")
        return "Unknown Window"

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    import sys
    import os
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
