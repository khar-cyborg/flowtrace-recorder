# FlowTrace Distribution Guide

## Building the Executable
To build FlowTrace as a standalone `.exe`, use PyInstaller with the provided spec file:

```powershell
pyinstaller MyCoolApp.spec
```

The resulting executable will be in the `dist` folder.

## Distributing to End Users
When sharing the `dist/FlowTrace.exe` (or the folder) with other users:

### 1. First Run & Browser Installation
If the user intends to use the **"Web (Playwright)"** mode or the **"Codegen"** feature, they need the Playwright browser binaries. These are NOT bundled inside the EXE to keep the file size manageable (~300MB difference).

**Instructions for the User:**
1. Open `FlowTrace`.
2. Select **"Web (Playwright)"** mode in the Settings area.
3. Click the **"⬇ Install Browsers"** button that appears.
4. Wait for the "Success" message indicating that browsers have been downloaded.

### 2. Troubleshooting
If the installation fails or the button doesn't work:
- Ensure the user has internet access.
- The app downloads a private copy of Chromium, Firefox, and WebKit managed by the Playwright library.

## For Developers: How it Works
- The "Install Browsers" button launches a subprocess: `FlowTrace.exe -m playwright install chromium`.
- `main.py` intercepts these arguments and redirects them to `playwright.main()`.
