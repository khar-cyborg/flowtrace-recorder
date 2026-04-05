# FlowTrace

**Test Evidence Recorder for QA Testers & Automation Engineers**

FlowTrace is a modern Windows desktop application that records your test sessions — capturing mouse clicks, keyboard input, and screenshots — and exports them as professional documentation (DOCX, PDF, HTML) or automation scripts (PyAutoGUI, Playwright Codegen). One recording session produces **both** test documentation **and** automation artifacts.

---

## Features

- **Desktop Recording** — Automatic capture of mouse clicks, keyboard input, and full-screen screenshots.
- **Web Recording** — Playwright-powered browser recording that extracts reusable CSS selectors.
- **Image Annotation** — Draw highlight rectangles directly on captured screenshots.
- **Step Management** — Reorder, edit descriptions, add text-only notes, and delete steps before export.
- **Multi-Format Export**
  - **DOCX** — Styled Word report with headers, footers, and embedded screenshots.
  - **PDF** — Print-ready document with page numbers and metadata.
  - **HTML** — Single self-contained file with base64-embedded images.
  - **PyAutoGUI** — Executable Python script that replays your recorded actions.
- **AI Prompt Library** — 17 curated prompts across 8 categories (screenshots, tracing, codegen, API testing, accessibility, etc.) that you can copy into ChatGPT / Claude to generate Playwright test code.
- **Floating Control Panel** — Transparent, always-on-top recording bar with live timer, manual snapshot, and note buttons.
- **Codegen Launcher** — Launch Playwright's built-in `codegen` tool directly from the app.

---

## Requirements

- **OS:** Windows 10 / 11
- **Python:** 3.9 or newer
- **Disk:** ~300 MB for Playwright browsers (optional, only for Web mode)

### Python dependencies
```
customtkinter
pynput
Pillow
python-docx
reportlab
pywin32
mss
packaging
playwright
```

---

## Installation (Development)

```powershell
# 1. Clone or download the repo
cd FlowTrace_Source_code

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. (Optional) Install Playwright browsers — only needed for Web Mode / Codegen
python -m playwright install chromium

# 5. Run the app
python main.py
```

---

## Usage

### Desktop Recording
1. Launch FlowTrace (`python main.py`).
2. Select **Desktop** mode.
3. Enter your **Tester** name and choose an **Output** folder.
4. Click **Start Recording**. The main window hides and a floating control panel appears.
5. Perform your test — every click is captured automatically with a screenshot. Use **⎙** for a manual snapshot or **✎** to add a note.
6. Click **Stop**. The **Review & Export** window opens.
7. Reorder / annotate / edit steps, then click **DOCX**, **PDF**, **HTML**, or **PyAutoGUI** to export.

### Web Recording
1. Select **Web** mode and enter a **URL**.
2. Click **Start Recording** — a Chromium browser opens.
3. Perform your test in the browser; FlowTrace captures clicks with CSS selectors + screenshots.
4. Close the browser or press **Stop**, then export as usual.
5. Or click **Codegen** to launch Playwright's interactive script generator.

### Prompt Library
Click **Prompt Library** in the header to browse 17 Playwright automation prompts. Search by keyword, filter by category, and click **Copy** to paste into any AI tool.

---

## Building a Standalone EXE

```powershell
pip install pyinstaller
pyinstaller --onefile --windowed --name FlowTrace main.py
```

The EXE appears in `dist/FlowTrace.exe`. See `DISTRIBUTION_GUIDE.md` for details on distributing to end users and first-run browser installation.

---

## Project Structure

```
FlowTrace_Source_code/
├── main.py                   # Entry point; handles CLI args & codegen mode
├── requirements.txt          # Python dependencies
├── .gitignore
├── DISTRIBUTION_GUIDE.md     # Instructions for distributing the EXE
├── FlowTrace_Demo.pptx       # Client demo presentation
└── app/
    ├── __init__.py
    ├── ui.py                 # CustomTkinter UI (main window, review, prompt library, editor)
    ├── recorder.py           # Core recording engine (desktop + web dispatch)
    ├── web_recorder.py       # Playwright-based browser recording
    ├── exporter.py           # DOCX / PDF / HTML / PyAutoGUI exporters
    ├── prompts.py            # AI prompt library content
    └── utils.py              # Helper functions (window title, resource path)
```

---

## Architecture Overview

- **`main.py`** — Bootstraps the app, handles `--codegen <url>` CLI mode, and logs fatal errors to `~/Documents/flowtrace_error.log`.
- **`Recorder`** — Owns the step list with a thread-safe `RLock`. Starts `pynput` listeners (desktop) or delegates to `WebRecorder` (web). Debounces auto-captures with a configurable `capture_delay`.
- **`WebRecorder`** — Runs Playwright in a background thread, injects a JavaScript preload script that generates CSS selectors, and calls back into Python via `expose_binding`.
- **`ui.py`** — A single-file modular UI with a shared design system (colors, fonts, radii). Key classes:
  - `FlowTraceApp` — Main window with mode cards, settings, and controls.
  - `FloatingControl` — Transparent always-on-top recording panel (uses Windows `transparentcolor`).
  - `ReviewWindow` — Step list with inline editing, reordering, and export buttons.
  - `PromptLibraryWindow` — Searchable, category-filtered prompt browser.
  - `ImageEditor` — Canvas-based annotation tool with undo history.
- **`exporter.py`** — Five format-specific export functions. Handles note-only steps (empty `image_bytes`) gracefully in every format.

---

## Version

**v2.0** — Modernized UI, prompt library, HTML export, note support, capture throttling.

---

## License

Internal / proprietary.
