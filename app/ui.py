import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
from app.recorder import Recorder
from app.exporter import export_docx, export_pdf, export_pyautogui, export_playwright, export_html
from app.prompts import PROMPT_CATEGORIES
from app.utils import resource_path
from PIL import Image, ImageDraw
import io
import tkinter as tk
import subprocess
import sys

# ═══════════════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM  —  Premium Dark Theme
# ═══════════════════════════════════════════════════════════════════════════

# ── Surfaces (layered depth) ───────────────────────────────────────────────
BG_PRIMARY      = "#0A0D14"   # App background (deepest)
BG_SECONDARY    = "#0F1219"   # Secondary surfaces
BG_CARD         = "#13161F"   # Card background
BG_CARD_HOVER   = "#181C27"   # Card hover state
BG_ELEVATED     = "#1A1E29"   # Elevated bars (toolbars, status)
BG_SURFACE      = "#222840"   # Interactive surfaces (ghost buttons)
BG_SURFACE_HOVER = "#2A3150"  # Interactive hover
BG_INPUT        = "#0E1119"   # Input fields

# ── Borders ────────────────────────────────────────────────────────────────
BORDER_SUBTLE   = "#1A2030"   # Very subtle dividers
BORDER_DEFAULT  = "#252D42"   # Standard borders
BORDER_STRONG   = "#303A55"   # Stronger borders
BORDER_ACTIVE   = "#4F8EF7"   # Active/focus borders

# ── Text ───────────────────────────────────────────────────────────────────
TEXT_PRIMARY    = "#EDF0F7"   # Primary text (near white)
TEXT_SECONDARY  = "#8892A8"   # Secondary text (muted)
TEXT_TERTIARY   = "#525C72"   # Tertiary text (dimmed)
TEXT_DISABLED   = "#363D50"   # Disabled text

# ── Accents ────────────────────────────────────────────────────────────────
ACCENT_BLUE         = "#4F8EF7"
ACCENT_BLUE_HOVER   = "#3D7AE5"
ACCENT_BLUE_MUTED   = "#141D33"   # Subtle blue tint (selected cards)

ACCENT_GREEN        = "#34D399"
ACCENT_GREEN_HOVER  = "#22C088"

ACCENT_RED          = "#F87171"
ACCENT_RED_HOVER    = "#EF5353"

ACCENT_AMBER        = "#FBBF24"
ACCENT_AMBER_HOVER  = "#EAA90E"

ACCENT_PURPLE       = "#A78BFA"
ACCENT_PURPLE_HOVER = "#9270F0"

ACCENT_TEAL         = "#2DD4BF"
ACCENT_TEAL_HOVER   = "#20C0AB"

ACCENT_PINK         = "#F472B6"

# ── Typography ─────────────────────────────────────────────────────────────
FONT_FAMILY     = "Segoe UI"
FONT_TITLE      = (FONT_FAMILY, 26, "bold")
FONT_HEADING    = (FONT_FAMILY, 16, "bold")
FONT_SUBHEAD    = (FONT_FAMILY, 13, "bold")
FONT_BODY       = (FONT_FAMILY, 12)
FONT_BODY_BOLD  = (FONT_FAMILY, 12, "bold")
FONT_CAPTION    = (FONT_FAMILY, 10)
FONT_SMALL      = (FONT_FAMILY, 9)
FONT_MONO       = ("Consolas", 11)
FONT_TIMER      = ("Consolas", 13, "bold")
FONT_ICON_LG    = (FONT_FAMILY, 22)
FONT_ICON_MD    = (FONT_FAMILY, 16)
FONT_BUTTON     = (FONT_FAMILY, 13, "bold")

# ── Radii ──────────────────────────────────────────────────────────────────
RADIUS_LG       = 14
RADIUS_MD       = 10
RADIUS_SM       = 8
RADIUS_XS       = 6
RADIUS_PILL     = 20

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


# ═══════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _bind_recursive(widget, event, callback):
    """Bind an event to widget and all its descendants."""
    widget.bind(event, callback)
    for child in widget.winfo_children():
        _bind_recursive(child, event, callback)


class Tooltip:
    """Lightweight tooltip that appears on hover."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event):
        if self.tip:
            return
        self.tip = ctk.CTkToplevel(self.widget)
        self.tip.overrideredirect(True)
        self.tip.attributes("-topmost", True)
        self.tip.geometry(f"+{event.x_root + 12}+{event.y_root + 22}")
        lbl = ctk.CTkLabel(self.tip, text=self.text, font=FONT_CAPTION,
                           fg_color=BG_ELEVATED, corner_radius=6,
                           text_color=TEXT_PRIMARY, padx=10, pady=5)
        lbl.pack()

    def _hide(self, event):
        if self.tip:
            self.tip.destroy()
            self.tip = None


def _gradient_bar(parent, height=3):
    """Create a horizontal blue→purple gradient accent bar."""
    bar = tk.Frame(parent, height=height, bg=BG_PRIMARY, bd=0, highlightthickness=0)
    bar.pack_propagate(False)
    colors = ["#3B82F6", "#5470F0", "#6B5EE8", "#8450E5", "#9D43E2", "#A855F7"]
    for c in colors:
        seg = tk.Frame(bar, bg=c, bd=0, highlightthickness=0)
        seg.pack(side="left", fill="both", expand=True)
    return bar


def _section_header(parent, title, pady=(2, 8)):
    """Render a small section header with accent marker."""
    header = ctk.CTkFrame(parent, fg_color="transparent")
    header.pack(fill="x", pady=pady)

    # Small colored accent bar
    accent = ctk.CTkFrame(header, width=3, height=14, fg_color=ACCENT_BLUE,
                          corner_radius=2)
    accent.pack(side="left", padx=(0, 8))

    ctk.CTkLabel(header, text=title, font=FONT_SUBHEAD,
                 text_color=TEXT_PRIMARY).pack(side="left")
    return header


# ═══════════════════════════════════════════════════════════════════════════
#  FLOATING RECORDING CONTROL
# ═══════════════════════════════════════════════════════════════════════════

class FloatingControl(ctk.CTkToplevel):
    def __init__(self, master, stop_callback, snapshot_callback, note_callback,
                 recorder, show_timer=True):
        super().__init__(master)
        self.title("Controls")
        self.recorder = recorder
        self._show_timer = show_timer

        width = 310 if show_timer else 240
        height = 60

        screen_width = self.winfo_screenwidth()
        x = screen_width - width - 30
        y = 30

        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.overrideredirect(True)

        # Transparent chrome — only the inner card is visible
        TRANSPARENT_KEY = "#010101"
        self.configure(fg_color=TRANSPARENT_KEY)
        if sys.platform == "win32":
            self.attributes("-transparentcolor", TRANSPARENT_KEY)
        else:
            self.attributes("-alpha", 0.92)

        # Subtle glow frame (outer layer)
        self.outer = ctk.CTkFrame(self, corner_radius=RADIUS_LG,
                                  fg_color=BORDER_ACTIVE)
        self.outer.pack(fill="both", expand=True, padx=2, pady=2)

        # Main card
        self.frame = ctk.CTkFrame(self.outer, corner_radius=RADIUS_LG - 2,
                                  fg_color=BG_CARD)
        self.frame.pack(fill="both", expand=True, padx=1, pady=1)

        # Draggable
        self.frame.bind("<Button-1>", self._start_move)
        self.frame.bind("<ButtonRelease-1>", self._stop_move)
        self.frame.bind("<B1-Motion>", self._do_move)

        # ── Left: action buttons ──
        btn_group = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_group.pack(side="left", padx=(10, 4), pady=8)

        self.snapshot_btn = ctk.CTkButton(
            btn_group, text="⎙", width=36, height=36,
            corner_radius=RADIUS_SM, fg_color=BG_SURFACE,
            hover_color=ACCENT_BLUE, font=(FONT_FAMILY, 16),
            text_color=TEXT_PRIMARY, command=snapshot_callback)
        self.snapshot_btn.pack(side="left", padx=2)
        Tooltip(self.snapshot_btn, "Capture Screenshot")

        self.note_btn = ctk.CTkButton(
            btn_group, text="✎", width=36, height=36,
            corner_radius=RADIUS_SM, fg_color=BG_SURFACE,
            hover_color=ACCENT_BLUE, font=(FONT_FAMILY, 16),
            text_color=TEXT_PRIMARY, command=note_callback)
        self.note_btn.pack(side="left", padx=2)
        Tooltip(self.note_btn, "Add Note")

        # ── Divider ──
        divider = ctk.CTkFrame(self.frame, width=1, fg_color=BORDER_DEFAULT)
        divider.pack(side="left", fill="y", padx=4, pady=14)

        # ── Center: recording indicator + timer ──
        center = ctk.CTkFrame(self.frame, fg_color="transparent")
        center.pack(side="left", expand=True, padx=6)

        indicator_row = ctk.CTkFrame(center, fg_color="transparent")
        indicator_row.pack()

        # Recording indicator dot with pulse effect
        self.rec_dot = ctk.CTkLabel(indicator_row, text="●", text_color=ACCENT_RED,
                                    font=(FONT_FAMILY, 14), width=16)
        self.rec_dot.pack(side="left")

        if show_timer:
            self.timer_label = ctk.CTkLabel(
                indicator_row, text="00:00",
                font=FONT_TIMER, text_color=TEXT_PRIMARY, width=58)
            self.timer_label.pack(side="left", padx=(4, 0))
        else:
            self.timer_label = None
            ctk.CTkLabel(indicator_row, text="REC",
                         font=(FONT_FAMILY, 10, "bold"),
                         text_color=TEXT_SECONDARY).pack(side="left", padx=(6, 0))

        # ── Right: stop button ──
        self.stop_btn = ctk.CTkButton(
            self.frame, text="■  Stop", width=78, height=36,
            corner_radius=RADIUS_SM, font=FONT_BODY_BOLD,
            fg_color=ACCENT_RED, hover_color=ACCENT_RED_HOVER,
            text_color="#FFFFFF", command=stop_callback)
        self.stop_btn.pack(side="right", padx=(4, 10), pady=8)

        self._drag_x = 0
        self._drag_y = 0
        self._blink_on = True
        self._blink_timer()
        if show_timer:
            self._update_timer()

    def _blink_timer(self):
        self._blink_on = not self._blink_on
        self.rec_dot.configure(text_color=ACCENT_RED if self._blink_on else BG_CARD)
        self.after(700, self._blink_timer)

    def _update_timer(self):
        try:
            self.timer_label.configure(text=self.recorder.get_elapsed_time())
        except Exception:
            pass
        self.after(1000, self._update_timer)

    def _start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _stop_move(self, event):
        self._drag_x = self._drag_y = 0

    def _do_move(self, event):
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")


# ═══════════════════════════════════════════════════════════════════════════
#  IMAGE ANNOTATION EDITOR
# ═══════════════════════════════════════════════════════════════════════════

class ImageEditor(ctk.CTkToplevel):
    def __init__(self, master, step, callback):
        super().__init__(master)
        self.title("FlowTrace — Annotate Image")
        self.geometry("980x740")
        self.configure(fg_color=BG_PRIMARY)
        self.step = step
        self.callback = callback

        # Load Image
        self.image_pil = Image.open(io.BytesIO(step.image_bytes))
        self.draw_pil = ImageDraw.Draw(self.image_pil)
        self.history = []

        # ── Toolbar ──
        toolbar = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=58)
        toolbar.pack(fill="x", side="top")
        toolbar.pack_propagate(False)

        # Toolbar inner
        tb_inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        tb_inner.pack(fill="both", expand=True, padx=20)

        # Title + hint
        title_box = ctk.CTkFrame(tb_inner, fg_color="transparent")
        title_box.pack(side="left", pady=10)

        accent = ctk.CTkFrame(title_box, width=3, height=28, fg_color=ACCENT_AMBER,
                              corner_radius=2)
        accent.pack(side="left", padx=(0, 10))

        text_col = ctk.CTkFrame(title_box, fg_color="transparent")
        text_col.pack(side="left")

        ctk.CTkLabel(text_col, text="Annotation Tool", font=FONT_SUBHEAD,
                     text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(text_col, text="Click and drag to draw highlight rectangles",
                     font=FONT_CAPTION, text_color=TEXT_TERTIARY).pack(anchor="w")

        # Actions
        ctk.CTkButton(tb_inner, text="✓  Save & Close", width=130, height=34,
                      corner_radius=RADIUS_SM, font=FONT_BODY_BOLD,
                      fg_color=ACCENT_GREEN, hover_color=ACCENT_GREEN_HOVER,
                      text_color="#0A0D14",
                      command=self.save_and_close).pack(side="right", padx=(4, 0), pady=12)
        ctk.CTkButton(tb_inner, text="↶ Undo", width=74, height=34,
                      corner_radius=RADIUS_SM, font=FONT_BODY,
                      fg_color=BG_SURFACE, hover_color=BG_SURFACE_HOVER,
                      text_color=TEXT_PRIMARY,
                      command=self.undo).pack(side="right", padx=4, pady=12)

        # Thin accent line under toolbar
        ctk.CTkFrame(self, fg_color=BORDER_DEFAULT, height=1,
                     corner_radius=0).pack(fill="x")

        # ── Canvas frame ──
        canvas_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=RADIUS_MD,
                                    border_width=1, border_color=BORDER_DEFAULT)
        canvas_frame.pack(fill="both", expand=True, padx=16, pady=16)

        self.canvas = tk.Canvas(canvas_frame, bg="#080A10",
                                highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True, padx=1, pady=1)

        from PIL import ImageTk
        self.tk_image = ImageTk.PhotoImage(self.image_pil)
        self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")

        self.start_x = self.start_y = None
        self.rect_id = None
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="#FF4444", width=3, dash=(6, 3))

    def on_drag(self, event):
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        self.history.append(self.image_pil.copy())
        self.draw_pil.rectangle([self.start_x, self.start_y, event.x, event.y],
                                outline="red", width=3)
        self.start_x = self.rect_id = None
        self._refresh_canvas()

    def undo(self):
        if not self.history:
            return
        self.image_pil = self.history.pop()
        self.draw_pil = ImageDraw.Draw(self.image_pil)
        self._refresh_canvas()

    def _refresh_canvas(self):
        from PIL import ImageTk
        self.tk_image = ImageTk.PhotoImage(self.image_pil)
        self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")

    def save_and_close(self):
        b = io.BytesIO()
        self.image_pil.save(b, format="PNG")
        self.step.image_bytes = b.getvalue()
        self.callback()
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════
#  REVIEW WINDOW
# ═══════════════════════════════════════════════════════════════════════════

class ReviewWindow(ctk.CTkToplevel):
    def __init__(self, master, recorder, app_instance):
        super().__init__(master)
        self.title("FlowTrace — Review & Export")
        self.geometry("960x740")
        self.configure(fg_color=BG_PRIMARY)
        self.recorder = recorder
        self.app = app_instance
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.minsize(820, 560)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Top bar ──
        top_bar = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=68)
        top_bar.grid(row=0, column=0, sticky="ew")
        top_bar.grid_propagate(False)

        top_inner = ctk.CTkFrame(top_bar, fg_color="transparent")
        top_inner.pack(fill="both", expand=True, padx=24)

        # Left: title + count
        title_col = ctk.CTkFrame(top_inner, fg_color="transparent")
        title_col.pack(side="left", pady=14)

        accent = ctk.CTkFrame(title_col, width=3, height=38, fg_color=ACCENT_BLUE,
                              corner_radius=2)
        accent.pack(side="left", padx=(0, 12))

        text_col = ctk.CTkFrame(title_col, fg_color="transparent")
        text_col.pack(side="left")

        title_row = ctk.CTkFrame(text_col, fg_color="transparent")
        title_row.pack(anchor="w")

        ctk.CTkLabel(title_row, text="Review Steps", font=FONT_HEADING,
                     text_color=TEXT_PRIMARY).pack(side="left")

        self.step_count_label = ctk.CTkLabel(
            title_row, text="0", font=FONT_CAPTION,
            text_color=ACCENT_BLUE, fg_color=ACCENT_BLUE_MUTED,
            corner_radius=RADIUS_PILL, padx=10, pady=2)
        self.step_count_label.pack(side="left", padx=8)

        ctk.CTkLabel(text_col, text="Edit, reorder, annotate and delete captured steps",
                     font=FONT_CAPTION, text_color=TEXT_TERTIARY).pack(anchor="w")

        # Right: Add Note
        ctk.CTkButton(top_inner, text="+ Add Note", width=110, height=34,
                      corner_radius=RADIUS_SM, font=FONT_BODY_BOLD,
                      fg_color=ACCENT_BLUE, hover_color=ACCENT_BLUE_HOVER,
                      text_color="#FFFFFF",
                      command=self.add_note).pack(side="right", pady=16)

        # Thin divider line
        ctk.CTkFrame(self, fg_color=BORDER_DEFAULT, height=1,
                     corner_radius=0).grid(row=0, column=0, sticky="ews")

        # ── Scrollable content ──
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color=BG_PRIMARY, corner_radius=0,
            scrollbar_button_color=BORDER_STRONG,
            scrollbar_button_hover_color=TEXT_TERTIARY)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(12, 0))

        # ── Bottom export bar ──
        bottom_wrap = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=72)
        bottom_wrap.grid(row=2, column=0, sticky="ews")
        bottom_wrap.grid_propagate(False)

        # Top divider of bottom bar
        ctk.CTkFrame(bottom_wrap, fg_color=BORDER_DEFAULT, height=1,
                     corner_radius=0).pack(fill="x")

        bottom_inner = ctk.CTkFrame(bottom_wrap, fg_color="transparent")
        bottom_inner.pack(fill="both", expand=True, padx=20)

        # Left: discard
        ctk.CTkButton(bottom_inner, text="Discard All", width=110, height=36,
                      corner_radius=RADIUS_SM, font=FONT_BODY,
                      fg_color="transparent", hover_color=ACCENT_RED,
                      border_width=1, border_color=ACCENT_RED,
                      text_color=ACCENT_RED, command=self.discard_all
                      ).pack(side="left", pady=17)

        # Right: export buttons
        export_configs = [
            ("PyAutoGUI",  "py",   ACCENT_GREEN,  ACCENT_GREEN_HOVER,  "#0A0D14"),
            ("HTML",       "html", ACCENT_PURPLE, ACCENT_PURPLE_HOVER, "#FFFFFF"),
            ("PDF",        "pdf",  ACCENT_AMBER,  ACCENT_AMBER_HOVER,  "#0A0D14"),
            ("DOCX",       "docx", ACCENT_BLUE,   ACCENT_BLUE_HOVER,   "#FFFFFF"),
        ]
        for label, fmt, fg, hover, txt_col in export_configs:
            ctk.CTkButton(
                bottom_inner, text=label, width=94, height=36,
                corner_radius=RADIUS_SM, font=FONT_BODY_BOLD,
                fg_color=fg, hover_color=hover, text_color=txt_col,
                command=lambda f=fmt: self.app.export(f)
            ).pack(side="right", padx=4, pady=17)

        ctk.CTkLabel(bottom_inner, text="Export as", font=FONT_CAPTION,
                     text_color=TEXT_TERTIARY).pack(side="right", padx=(0, 12))

        self.refresh_list()

    def refresh_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        steps = self.recorder.get_steps()
        self.step_count_label.configure(text=str(len(steps)))

        if not steps:
            empty = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            empty.pack(pady=80, fill="x")

            icon_box = ctk.CTkFrame(empty, width=72, height=72, fg_color=BG_CARD,
                                    corner_radius=RADIUS_LG, border_width=1,
                                    border_color=BORDER_DEFAULT)
            icon_box.pack()
            icon_box.pack_propagate(False)
            ctk.CTkLabel(icon_box, text="○", font=(FONT_FAMILY, 32),
                         text_color=TEXT_TERTIARY).pack(expand=True)

            ctk.CTkLabel(empty, text="No steps captured",
                         font=FONT_HEADING,
                         text_color=TEXT_SECONDARY).pack(pady=(16, 6))
            ctk.CTkLabel(empty, text="Start a recording session to capture test evidence",
                         font=FONT_BODY, text_color=TEXT_TERTIARY).pack()
            return

        total = len(steps)
        for i, step in enumerate(steps):
            self._create_step_card(i, step, total)

    def _create_step_card(self, index, step, total):
        is_note = not step.image_bytes

        border_col = ACCENT_AMBER if is_note else BORDER_DEFAULT
        card = ctk.CTkFrame(self.scroll_frame, corner_radius=RADIUS_MD,
                            fg_color=BG_CARD, border_width=1,
                            border_color=border_col)
        card.pack(fill="x", pady=5, padx=2)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)

        # ── Step badge (circle with number) ──
        badge_col = ACCENT_AMBER if is_note else ACCENT_BLUE
        badge = ctk.CTkFrame(inner, width=34, height=34, fg_color=badge_col,
                             corner_radius=17)
        badge.pack(side="left", padx=(0, 12))
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text=str(index + 1), font=FONT_BODY_BOLD,
                     text_color="#0A0D14" if is_note else "#FFFFFF").pack(expand=True)

        # ── Thumbnail / note icon ──
        if is_note:
            icon_frame = ctk.CTkFrame(inner, width=92, height=64, fg_color=BG_ELEVATED,
                                      corner_radius=RADIUS_SM, border_width=1,
                                      border_color=BORDER_DEFAULT)
            icon_frame.pack(side="left", padx=(0, 12))
            icon_frame.pack_propagate(False)
            ctk.CTkLabel(icon_frame, text="✎", font=(FONT_FAMILY, 24),
                         text_color=ACCENT_AMBER).pack(expand=True)
        else:
            try:
                image = Image.open(io.BytesIO(step.image_bytes))
                image.thumbnail((120, 70))
                ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
                thumb = ctk.CTkLabel(inner, image=ctk_image, text="",
                                     corner_radius=RADIUS_XS)
                thumb.pack(side="left", padx=(0, 12))
            except Exception:
                placeholder = ctk.CTkFrame(inner, width=92, height=64,
                                           fg_color=BG_ELEVATED, corner_radius=RADIUS_SM,
                                           border_width=1, border_color=BORDER_DEFAULT)
                placeholder.pack(side="left", padx=(0, 12))
                placeholder.pack_propagate(False)
                ctk.CTkLabel(placeholder, text="No img", font=FONT_CAPTION,
                             text_color=TEXT_TERTIARY).pack(expand=True)

        # ── Center: info ──
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=(0, 8))

        header = ctk.CTkFrame(info, fg_color="transparent")
        header.pack(fill="x")

        label_text = f"Step {index + 1}" + ("  ·  Note" if is_note else "")
        ctk.CTkLabel(header, text=label_text, font=FONT_BODY_BOLD,
                     text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header, text=step.timestamp, font=FONT_SMALL,
                     text_color=TEXT_TERTIARY).pack(side="right")

        entry = ctk.CTkEntry(info, font=FONT_BODY, height=32,
                             corner_radius=RADIUS_XS,
                             fg_color=BG_INPUT, border_width=1,
                             border_color=BORDER_DEFAULT,
                             text_color=TEXT_PRIMARY)
        entry.insert(0, step.description)
        entry.pack(fill="x", pady=(6, 0))
        entry.bind("<FocusOut>",
                   lambda e, idx=index, ent=entry: self.update_description(idx, ent.get()))

        # ── Right: action buttons ──
        actions = ctk.CTkFrame(inner, fg_color="transparent", width=40)
        actions.pack(side="right")

        btn_style = dict(width=34, height=26, corner_radius=RADIUS_XS,
                         font=FONT_CAPTION, text_color=TEXT_PRIMARY)

        up_btn = ctk.CTkButton(
            actions, text="▲", fg_color=BG_SURFACE, hover_color=BG_SURFACE_HOVER,
            command=lambda: self.move_step(index, -1),
            state="normal" if index > 0 else "disabled", **btn_style)
        up_btn.pack(pady=1)
        Tooltip(up_btn, "Move Up")

        dn_btn = ctk.CTkButton(
            actions, text="▼", fg_color=BG_SURFACE, hover_color=BG_SURFACE_HOVER,
            command=lambda: self.move_step(index, 1),
            state="normal" if index < total - 1 else "disabled", **btn_style)
        dn_btn.pack(pady=1)
        Tooltip(dn_btn, "Move Down")

        if not is_note:
            an_btn = ctk.CTkButton(
                actions, text="✎", fg_color=BG_SURFACE, hover_color=ACCENT_AMBER,
                command=lambda: self.open_annotation(index), **btn_style)
            an_btn.pack(pady=1)
            Tooltip(an_btn, "Annotate")

        del_btn = ctk.CTkButton(
            actions, text="✕", fg_color=BG_SURFACE, hover_color=ACCENT_RED,
            command=lambda: self.delete_step(index), **btn_style)
        del_btn.pack(pady=1)
        Tooltip(del_btn, "Delete")

    def move_step(self, index, direction):
        if self.recorder.move_step(index, direction):
            self.refresh_list()

    def add_note(self):
        dialog = ctk.CTkInputDialog(text="Enter a note:", title="Add Note")
        text = dialog.get_input()
        if text:
            self.recorder.add_note(text)
            self.refresh_list()

    def open_annotation(self, index):
        step = self.recorder.get_steps()[index]
        ImageEditor(self, step, self.refresh_list)

    def update_description(self, index, text):
        self.recorder.update_step(index, text)

    def delete_step(self, index):
        self.recorder.delete_step(index)
        self.refresh_list()

    def discard_all(self):
        if messagebox.askyesno("Discard", "Are you sure you want to discard all steps?"):
            self.recorder.clear()
            self.on_close()

    def on_close(self):
        self.destroy()
        self.app.deiconify()


# ═══════════════════════════════════════════════════════════════════════════
#  PROMPT LIBRARY WINDOW
# ═══════════════════════════════════════════════════════════════════════════

class PromptLibraryWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("FlowTrace — Prompt Library")
        self.geometry("900x740")
        self.configure(fg_color=BG_PRIMARY)
        self.minsize(760, 540)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Top bar ──
        top_bar = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=110)
        top_bar.grid(row=0, column=0, sticky="ew")
        top_bar.grid_propagate(False)

        top_inner = ctk.CTkFrame(top_bar, fg_color="transparent")
        top_inner.pack(fill="both", expand=True, padx=24, pady=16)

        # Title row
        title_row = ctk.CTkFrame(top_inner, fg_color="transparent")
        title_row.pack(fill="x")

        accent = ctk.CTkFrame(title_row, width=3, height=32, fg_color=ACCENT_PURPLE,
                              corner_radius=2)
        accent.pack(side="left", padx=(0, 12))

        text_col = ctk.CTkFrame(title_row, fg_color="transparent")
        text_col.pack(side="left")

        ctk.CTkLabel(text_col, text="Prompt Library", font=FONT_HEADING,
                     text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(text_col,
                     text="Copy any prompt and paste into ChatGPT, Claude or any AI tool",
                     font=FONT_CAPTION, text_color=TEXT_TERTIARY).pack(anchor="w")

        # Count badge
        total_prompts = sum(len(v) for v in PROMPT_CATEGORIES.values())
        ctk.CTkLabel(title_row, text=f"{total_prompts} prompts",
                     font=FONT_CAPTION, text_color=ACCENT_PURPLE,
                     fg_color=BG_CARD, corner_radius=RADIUS_PILL,
                     padx=12, pady=4).pack(side="right")

        # Search + filter row
        filter_row = ctk.CTkFrame(top_inner, fg_color="transparent")
        filter_row.pack(fill="x", pady=(12, 0))

        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            filter_row, textvariable=self.search_var, height=34,
            placeholder_text="   Search prompts by name or description...",
            corner_radius=RADIUS_SM, font=FONT_BODY,
            fg_color=BG_INPUT, border_width=1, border_color=BORDER_DEFAULT,
            text_color=TEXT_PRIMARY)
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_var.trace_add("write", lambda *_: self._render_prompts())

        # Category filter
        categories = ["All Categories"] + list(PROMPT_CATEGORIES.keys())
        self.category_var = tk.StringVar(value="All Categories")
        self.category_menu = ctk.CTkOptionMenu(
            filter_row, values=categories, variable=self.category_var,
            width=200, height=34, corner_radius=RADIUS_SM,
            font=FONT_BODY, fg_color=BG_SURFACE,
            button_color=BG_SURFACE, button_hover_color=ACCENT_PURPLE,
            text_color=TEXT_PRIMARY, dropdown_fg_color=BG_CARD,
            dropdown_hover_color=BG_SURFACE_HOVER,
            command=lambda _: self._render_prompts())
        self.category_menu.pack(side="right")

        # Divider
        ctk.CTkFrame(self, fg_color=BORDER_DEFAULT, height=1,
                     corner_radius=0).grid(row=0, column=0, sticky="ews")

        # ── Scrollable content ──
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG_PRIMARY, corner_radius=0,
            scrollbar_button_color=BORDER_STRONG,
            scrollbar_button_hover_color=TEXT_TERTIARY)
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(12, 16))

        self._render_prompts()

    def _render_prompts(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        selected = self.category_var.get()
        search = self.search_var.get().lower().strip()

        if selected == "All Categories":
            category_items = list(PROMPT_CATEGORIES.items())
        else:
            category_items = [(selected, PROMPT_CATEGORIES.get(selected, []))]

        # Apply search filter
        filtered_categories = []
        for cat_name, prompts in category_items:
            if search:
                matched = [
                    p for p in prompts
                    if search in p[0].lower() or search in p[1].lower()
                ]
                if matched:
                    filtered_categories.append((cat_name, matched))
            else:
                filtered_categories.append((cat_name, prompts))

        if not filtered_categories:
            empty = ctk.CTkFrame(self.scroll, fg_color="transparent")
            empty.pack(pady=60, fill="x")
            ctk.CTkLabel(empty, text="No prompts match your search",
                         font=FONT_SUBHEAD, text_color=TEXT_SECONDARY).pack()
            ctk.CTkLabel(empty, text="Try a different search term or category",
                         font=FONT_CAPTION, text_color=TEXT_TERTIARY).pack(pady=4)
            return

        for cat_name, prompts in filtered_categories:
            # Category header with badge
            cat_header = ctk.CTkFrame(self.scroll, fg_color="transparent")
            cat_header.pack(fill="x", pady=(18, 8), padx=2)

            dot = ctk.CTkFrame(cat_header, width=6, height=6, fg_color=ACCENT_PURPLE,
                               corner_radius=3)
            dot.pack(side="left", padx=(0, 10), pady=(0, 1))

            ctk.CTkLabel(cat_header, text=cat_name, font=FONT_SUBHEAD,
                         text_color=TEXT_PRIMARY).pack(side="left")

            ctk.CTkLabel(cat_header, text=f"{len(prompts)}",
                         font=FONT_SMALL, text_color=TEXT_TERTIARY,
                         fg_color=BG_CARD, corner_radius=RADIUS_PILL,
                         padx=8, pady=1).pack(side="left", padx=8)

            ctk.CTkFrame(cat_header, fg_color=BORDER_SUBTLE, height=1
                         ).pack(side="left", fill="x", expand=True, padx=(10, 0), pady=2)

            for title, description, prompt_text in prompts:
                self._create_prompt_card(title, description, prompt_text)

    def _create_prompt_card(self, title, description, prompt_text):
        card = ctk.CTkFrame(self.scroll, fg_color=BG_CARD,
                            corner_radius=RADIUS_MD,
                            border_width=1, border_color=BORDER_DEFAULT)
        card.pack(fill="x", pady=4, padx=2)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=14)

        # Header: title + copy button
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x")

        ctk.CTkLabel(header, text=title, font=FONT_BODY_BOLD,
                     text_color=TEXT_PRIMARY).pack(side="left")

        copy_btn = ctk.CTkButton(
            header, text="⎘  Copy", width=74, height=28,
            corner_radius=RADIUS_XS, font=FONT_CAPTION,
            fg_color=ACCENT_BLUE, hover_color=ACCENT_BLUE_HOVER,
            text_color="#FFFFFF",
            command=lambda: self._copy_prompt(prompt_text, copy_btn))
        copy_btn.pack(side="right")

        # Description
        ctk.CTkLabel(inner, text=description, font=FONT_CAPTION,
                     text_color=TEXT_SECONDARY, anchor="w",
                     wraplength=740, justify="left").pack(fill="x", pady=(4, 8))

        # Preview box (collapsed)
        preview_lines = prompt_text.strip().split("\n")[:3]
        preview_text = "\n".join(preview_lines)
        if len(prompt_text.strip().split("\n")) > 3:
            preview_text += "\n..."

        preview_frame = ctk.CTkFrame(inner, fg_color=BG_INPUT,
                                     corner_radius=RADIUS_XS, border_width=1,
                                     border_color=BORDER_SUBTLE)
        preview_frame.pack(fill="x")

        preview_label = ctk.CTkLabel(
            preview_frame, text=preview_text, font=FONT_MONO,
            text_color=TEXT_SECONDARY, anchor="nw", justify="left",
            wraplength=720)
        preview_label.pack(fill="x", padx=12, pady=9)

        # Expand toggle
        is_expanded = tk.BooleanVar(value=False)

        def toggle_expand():
            if is_expanded.get():
                preview_label.configure(text=preview_text)
                expand_btn.configure(text="▾ Show full prompt")
                is_expanded.set(False)
            else:
                preview_label.configure(text=prompt_text.strip())
                expand_btn.configure(text="▴ Collapse")
                is_expanded.set(True)

        expand_btn = ctk.CTkButton(
            inner, text="▾ Show full prompt", width=140, height=24,
            corner_radius=RADIUS_XS, font=FONT_CAPTION,
            fg_color="transparent", hover_color=BG_SURFACE,
            text_color=ACCENT_BLUE, command=toggle_expand)
        expand_btn.pack(anchor="w", pady=(6, 0))

    def _copy_prompt(self, text, btn):
        self.clipboard_clear()
        self.clipboard_append(text.strip())
        btn.configure(text="✓ Copied", fg_color=ACCENT_GREEN)
        self.after(1500, lambda: btn.configure(text="⎘  Copy", fg_color=ACCENT_BLUE))


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION WINDOW
# ═══════════════════════════════════════════════════════════════════════════

class FlowTraceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FlowTrace")
        self.geometry("600x680")
        self.configure(fg_color=BG_PRIMARY)
        self.minsize(540, 620)

        self.recorder = Recorder()
        self.floating_panel = None
        self.mode_cards = {}
        self._setup_ui()

    # ── UI Setup ───────────────────────────────────────────────────────────
    def _setup_ui(self):
        # Top gradient accent bar
        _gradient_bar(self, height=3).pack(fill="x", side="top")

        # Bottom status bar (packed first to stay pinned)
        self._create_status_bar()

        # Main content container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=(16, 12))

        # ── Header ──
        self._create_header(container)

        # ── Mode selector cards ──
        self._create_mode_selector(container)

        # ── Configuration ──
        self._create_config_section(container)

        # ── Controls ──
        self._create_controls_section(container)

        # Initialize UI state
        self.toggle_mode_ui()
        self._update_mode_cards()
        self.update_step_counter()

    # ── Header ─────────────────────────────────────────────────────────────
    def _create_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 14))

        # Logo/title row
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x")

        # Logo mark — small colored square + title
        mark = ctk.CTkFrame(title_row, width=32, height=32, fg_color=ACCENT_BLUE,
                            corner_radius=RADIUS_SM)
        mark.pack(side="left", padx=(0, 12))
        mark.pack_propagate(False)
        ctk.CTkLabel(mark, text="✦", font=(FONT_FAMILY, 18, "bold"),
                     text_color="#FFFFFF").pack(expand=True)

        title_col = ctk.CTkFrame(title_row, fg_color="transparent")
        title_col.pack(side="left", fill="both", expand=True)

        title_line = ctk.CTkFrame(title_col, fg_color="transparent")
        title_line.pack(anchor="w")

        ctk.CTkLabel(title_line, text="FlowTrace", font=FONT_TITLE,
                     text_color=TEXT_PRIMARY).pack(side="left")

        ctk.CTkLabel(title_line, text="v2.0", font=FONT_SMALL,
                     text_color=ACCENT_BLUE, fg_color=ACCENT_BLUE_MUTED,
                     corner_radius=RADIUS_XS, padx=8, pady=2
                     ).pack(side="left", padx=10, pady=(6, 0))

        ctk.CTkLabel(title_col, text="Test Evidence Recorder",
                     font=FONT_CAPTION, text_color=TEXT_TERTIARY
                     ).pack(anchor="w", pady=(2, 0))

        # Prompt Library button (right)
        prompt_btn = ctk.CTkButton(
            title_row, text="✧  Prompt Library", width=140, height=34,
            corner_radius=RADIUS_SM, font=FONT_BODY,
            fg_color=BG_SURFACE, hover_color=ACCENT_PURPLE,
            text_color=TEXT_PRIMARY, command=self._open_prompt_library)
        prompt_btn.pack(side="right", pady=4)
        Tooltip(prompt_btn, "17 curated AI prompts for Playwright automation")

    # ── Mode Selector ──────────────────────────────────────────────────────
    def _create_mode_selector(self, parent):
        _section_header(parent, "Recording Mode")

        cards_wrap = ctk.CTkFrame(parent, fg_color="transparent")
        cards_wrap.pack(fill="x", pady=(0, 14))
        cards_wrap.grid_columnconfigure(0, weight=1)
        cards_wrap.grid_columnconfigure(1, weight=1)

        self.mode_var = tk.StringVar(value="desktop")

        self.mode_cards["desktop"] = self._make_mode_card(
            cards_wrap, 0, mode="desktop",
            icon="⊞", title="Desktop",
            desc="Record clicks, keys &\nscreenshots on any app")

        self.mode_cards["web"] = self._make_mode_card(
            cards_wrap, 1, mode="web",
            icon="◎", title="Web",
            desc="Playwright browser\nrecording with selectors")

    def _make_mode_card(self, parent, col, mode, icon, title, desc):
        card = ctk.CTkFrame(parent, fg_color=BG_CARD,
                            corner_radius=RADIUS_LG, border_width=1,
                            border_color=BORDER_DEFAULT, cursor="hand2",
                            height=88)
        card.grid(row=0, column=col, padx=6, sticky="nsew")
        card.pack_propagate(False)
        card.grid_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")

        icon_lbl = ctk.CTkLabel(top_row, text=icon, font=FONT_ICON_LG,
                                text_color=TEXT_TERTIARY, width=28)
        icon_lbl.pack(side="left")

        title_lbl = ctk.CTkLabel(top_row, text=title, font=FONT_SUBHEAD,
                                 text_color=TEXT_SECONDARY)
        title_lbl.pack(side="left", padx=(8, 0))

        # Active indicator (small dot on right) — uses card bg when inactive
        dot_lbl = ctk.CTkLabel(top_row, text="●", font=(FONT_FAMILY, 12),
                               text_color=BG_CARD, width=14)
        dot_lbl.pack(side="right")

        desc_lbl = ctk.CTkLabel(inner, text=desc, font=FONT_CAPTION,
                                text_color=TEXT_TERTIARY, anchor="w",
                                justify="left")
        desc_lbl.pack(anchor="w", pady=(4, 0))

        # Bind clicks to entire card
        def on_click(event):
            self._select_mode(mode)

        def on_enter(event):
            if self.mode_var.get() != mode:
                card.configure(fg_color=BG_CARD_HOVER, border_color=BORDER_STRONG)

        def on_leave(event):
            if self.mode_var.get() != mode:
                card.configure(fg_color=BG_CARD, border_color=BORDER_DEFAULT)

        _bind_recursive(card, "<Button-1>", on_click)
        _bind_recursive(card, "<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

        return {
            "frame": card, "icon": icon_lbl,
            "title": title_lbl, "desc": desc_lbl, "dot": dot_lbl
        }

    def _select_mode(self, mode):
        self.mode_var.set(mode)
        self._update_mode_cards()
        self.toggle_mode_ui()

    def _update_mode_cards(self):
        current = self.mode_var.get()
        for key, card in self.mode_cards.items():
            is_active = key == current
            if is_active:
                card["frame"].configure(
                    fg_color=ACCENT_BLUE_MUTED,
                    border_color=ACCENT_BLUE, border_width=2)
                card["icon"].configure(text_color=ACCENT_BLUE)
                card["title"].configure(text_color=TEXT_PRIMARY)
                card["desc"].configure(text_color=TEXT_SECONDARY)
                card["dot"].configure(text_color=ACCENT_BLUE)
            else:
                card["frame"].configure(
                    fg_color=BG_CARD,
                    border_color=BORDER_DEFAULT, border_width=1)
                card["icon"].configure(text_color=TEXT_TERTIARY)
                card["title"].configure(text_color=TEXT_SECONDARY)
                card["desc"].configure(text_color=TEXT_TERTIARY)
                card["dot"].configure(text_color=BG_CARD)

    # ── Configuration Section ──────────────────────────────────────────────
    def _create_config_section(self, parent):
        _section_header(parent, "Configuration")

        card = ctk.CTkFrame(parent, fg_color=BG_CARD,
                            corner_radius=RADIUS_LG,
                            border_width=1, border_color=BORDER_DEFAULT)
        card.pack(fill="x", pady=(0, 14))

        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=12)
        grid.grid_columnconfigure(1, weight=1)

        # Row 0: Tester Name
        self._form_label(grid, "Tester", 0)
        self.entry_name = self._form_entry(grid, placeholder="Enter tester name")
        self.entry_name.grid(row=0, column=1, columnspan=2, sticky="ew", pady=4)
        self.entry_name.insert(0, "QA Tester")

        # Row 1: Output Folder
        self._form_label(grid, "Output", 1)
        self.entry_path = self._form_entry(grid)
        self.entry_path.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=4)

        default_path = os.path.join(os.path.expanduser("~"), "Documents")
        if not os.path.exists(default_path):
            default_path = os.getcwd()
        self.entry_path.insert(0, default_path)

        self.btn_browse = ctk.CTkButton(
            grid, text="Browse", width=78, height=36,
            corner_radius=RADIUS_SM, font=FONT_BODY,
            fg_color=BG_SURFACE, hover_color=BG_SURFACE_HOVER,
            text_color=TEXT_PRIMARY, command=self.browse_folder)
        self.btn_browse.grid(row=1, column=2, pady=4)

        # Row 2 & 3: Web mode fields (hidden by default)
        self.lbl_url = ctk.CTkLabel(grid, text="URL", font=FONT_BODY,
                                    text_color=TEXT_SECONDARY, anchor="w", width=68)
        self.entry_url = self._form_entry(grid, placeholder="https://example.com")
        self.entry_url.insert(0, "https://google.com")

        self.btn_codegen = ctk.CTkButton(
            grid, text="Codegen", width=78, height=36,
            corner_radius=RADIUS_SM, font=FONT_BODY_BOLD,
            fg_color=ACCENT_AMBER, hover_color=ACCENT_AMBER_HOVER,
            text_color="#0A0D14", command=self.launch_codegen)

        self.btn_install_browsers = ctk.CTkButton(
            grid, text="Install Browsers", width=130, height=30,
            corner_radius=RADIUS_SM, font=FONT_CAPTION,
            fg_color=BG_SURFACE, hover_color=BG_SURFACE_HOVER,
            text_color=TEXT_SECONDARY, command=self.install_browsers)

    def _form_label(self, parent, text, row):
        ctk.CTkLabel(parent, text=text, font=FONT_BODY,
                     text_color=TEXT_SECONDARY, anchor="w", width=68
                     ).grid(row=row, column=0, padx=(0, 12), pady=4, sticky="w")

    def _form_entry(self, parent, placeholder=""):
        return ctk.CTkEntry(
            parent, font=FONT_BODY, height=36,
            corner_radius=RADIUS_SM,
            fg_color=BG_INPUT, border_width=1, border_color=BORDER_DEFAULT,
            text_color=TEXT_PRIMARY, placeholder_text=placeholder)

    # ── Controls Section ───────────────────────────────────────────────────
    def _create_controls_section(self, parent):
        _section_header(parent, "Controls")

        card = ctk.CTkFrame(parent, fg_color=BG_CARD,
                            corner_radius=RADIUS_LG,
                            border_width=1, border_color=BORDER_DEFAULT)
        card.pack(fill="x", pady=(0, 0))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        # Start button — large and prominent
        self.btn_start = ctk.CTkButton(
            inner, text="●  Start Recording", height=48,
            corner_radius=RADIUS_MD, font=(FONT_FAMILY, 15, "bold"),
            fg_color=ACCENT_GREEN, hover_color=ACCENT_GREEN_HOVER,
            text_color="#0A0D14", command=self.start_recording)
        self.btn_start.pack(fill="x", pady=(0, 12))

        # ── Options panel (checkboxes + slider in grouped container) ──
        options_panel = ctk.CTkFrame(inner, fg_color=BG_INPUT,
                                     corner_radius=RADIUS_SM,
                                     border_width=1, border_color=BORDER_DEFAULT)
        options_panel.pack(fill="x")

        # Checkboxes row
        cb_row = ctk.CTkFrame(options_panel, fg_color="transparent")
        cb_row.pack(fill="x", padx=14, pady=(10, 7))

        self.check_auto = ctk.CTkCheckBox(
            cb_row, text="Auto-capture",
            font=FONT_BODY, text_color=TEXT_PRIMARY,
            fg_color=ACCENT_BLUE, hover_color=ACCENT_BLUE_HOVER,
            checkbox_width=20, checkbox_height=20, corner_radius=4,
            border_color=BORDER_STRONG, border_width=2,
            onvalue=True, offvalue=False)
        self.check_auto.select()
        self.check_auto.pack(side="left")

        self.check_timer = ctk.CTkCheckBox(
            cb_row, text="Show timer",
            font=FONT_BODY, text_color=TEXT_PRIMARY,
            fg_color=ACCENT_BLUE, hover_color=ACCENT_BLUE_HOVER,
            checkbox_width=20, checkbox_height=20, corner_radius=4,
            border_color=BORDER_STRONG, border_width=2,
            onvalue=True, offvalue=False)
        self.check_timer.select()
        self.check_timer.pack(side="left", padx=(20, 0))

        # Thin divider between checkboxes and slider
        ctk.CTkFrame(options_panel, fg_color=BORDER_SUBTLE, height=1
                     ).pack(fill="x", padx=14)

        # Delay slider row
        delay_row = ctk.CTkFrame(options_panel, fg_color="transparent")
        delay_row.pack(fill="x", padx=14, pady=(7, 10))

        ctk.CTkLabel(delay_row, text="Capture delay", font=FONT_CAPTION,
                     text_color=TEXT_SECONDARY).pack(side="left")

        self.delay_label = ctk.CTkLabel(delay_row, text="0.3s",
                                        font=FONT_BODY_BOLD,
                                        text_color=ACCENT_BLUE, width=36)
        self.delay_label.pack(side="right")

        self.delay_slider = ctk.CTkSlider(
            delay_row, from_=0.1, to=2.0, number_of_steps=19,
            height=14, button_length=10, button_corner_radius=5,
            fg_color=BG_SURFACE, progress_color=ACCENT_BLUE,
            button_color=ACCENT_BLUE, button_hover_color=ACCENT_BLUE_HOVER,
            command=self._on_delay_change)
        self.delay_slider.set(0.3)
        self.delay_slider.pack(side="right", fill="x", expand=True, padx=12)

    # ── Status Bar (bottom, persistent) ───────────────────────────────────
    def _create_status_bar(self):
        # Thin divider above status bar
        divider = ctk.CTkFrame(self, fg_color=BORDER_DEFAULT, height=1,
                               corner_radius=0)
        divider.pack(fill="x", side="bottom")

        bar = ctk.CTkFrame(self, fg_color=BG_ELEVATED, height=36,
                           corner_radius=0)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20)

        # Left: status dot + text
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="y")

        self.status_dot = ctk.CTkLabel(left, text="●", font=(FONT_FAMILY, 10),
                                       text_color=ACCENT_GREEN, width=14)
        self.status_dot.pack(side="left", padx=(0, 6))

        self.status_label = ctk.CTkLabel(left, text="Ready", font=FONT_CAPTION,
                                         text_color=TEXT_SECONDARY)
        self.status_label.pack(side="left")

        # Right: step counter
        self.lbl_steps = ctk.CTkLabel(inner, text="0 steps",
                                      font=FONT_BODY_BOLD,
                                      text_color=ACCENT_BLUE,
                                      fg_color=ACCENT_BLUE_MUTED,
                                      corner_radius=RADIUS_PILL,
                                      padx=12, pady=2)
        self.lbl_steps.pack(side="right", pady=6)

    def _set_status(self, text, color=TEXT_SECONDARY, dot_color=ACCENT_GREEN):
        self.status_label.configure(text=text, text_color=color)
        self.status_dot.configure(text_color=dot_color)

    # ── Mode Toggle ────────────────────────────────────────────────────────
    def toggle_mode_ui(self):
        if self.mode_var.get() == "web":
            self.lbl_url.grid(row=2, column=0, padx=(0, 12), pady=4, sticky="w")
            self.entry_url.grid(row=2, column=1, padx=(0, 8), pady=4, sticky="ew")
            self.btn_codegen.grid(row=2, column=2, pady=4)
            self.btn_install_browsers.grid(row=3, column=1, columnspan=2,
                                           pady=(4, 2), sticky="e")
            self.check_auto.configure(state="disabled")
        else:
            self.lbl_url.grid_forget()
            self.entry_url.grid_forget()
            self.btn_codegen.grid_forget()
            self.btn_install_browsers.grid_forget()
            self.check_auto.configure(state="normal")

    # ── Browser Install ────────────────────────────────────────────────────
    def install_browsers(self):
        if not messagebox.askyesno(
                "Install Browsers",
                "This will download Playwright browsers (~150MB). Continue?"):
            return
        try:
            creationflags = 0x08000000 if sys.platform == "win32" else 0
            cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
            threading.Thread(target=self._run_install_browsers,
                             args=(cmd, creationflags), daemon=True).start()
            self._set_status("Installing browsers...", ACCENT_AMBER, ACCENT_AMBER)
            self.btn_install_browsers.configure(state="disabled", text="Installing...")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start installation: {e}")

    def _run_install_browsers(self, cmd, flags):
        try:
            subprocess.check_call(cmd, creationflags=flags)
            self.after(0, lambda: messagebox.showinfo("Success", "Browsers installed!"))
            self.after(0, lambda: self._set_status("Ready", TEXT_SECONDARY, ACCENT_GREEN))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Installation failed:\n{e}"))
        finally:
            self.after(0, lambda: self.btn_install_browsers.configure(
                state="normal", text="Install Browsers"))

    # ── Actions ────────────────────────────────────────────────────────────
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, folder)

    def _on_delay_change(self, value):
        value = round(value, 1)
        self.delay_label.configure(text=f"{value}s")
        self.recorder.capture_delay = value

    def start_recording(self):
        self.recorder.clear()
        auto = self.check_auto.get()
        mode = self.mode_var.get()
        url = self.entry_url.get()

        try:
            self.recorder.start(auto_capture=auto, mode=mode, url=url)
        except Exception as e:
            messagebox.showerror("Recording Error",
                                 f"Failed to start recording:\n{e}\n\n"
                                 "If using Web Mode, ensure Playwright browsers are installed.")
            self._set_status("Error", ACCENT_RED, ACCENT_RED)
            self.btn_start.configure(state="normal")
            return

        self.withdraw()
        self.floating_panel = FloatingControl(
            self, self.stop_recording, self.manual_snapshot,
            self.add_note_during_recording, self.recorder,
            show_timer=bool(self.check_timer.get()))
        self._set_status(f"Recording ({mode})...", ACCENT_RED, ACCENT_RED)
        self.btn_start.configure(state="disabled")

    def stop_recording(self):
        try:
            self.recorder.stop()
            if self.floating_panel:
                self.floating_panel.destroy()
                self.floating_panel = None
            self._set_status("Recording stopped", ACCENT_GREEN, ACCENT_GREEN)
            self.btn_start.configure(state="normal", text="●  Start Recording")
            self.review_window = ReviewWindow(self, self.recorder, self)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while stopping: {e}")
            self.btn_start.configure(state="normal", text="●  Start Recording")
            self.deiconify()

    def manual_snapshot(self):
        if self.floating_panel:
            self.floating_panel.withdraw()
            self.floating_panel.update()
        self.after(500, self._do_snapshot)

    def _do_snapshot(self):
        self.recorder.manual_capture()
        if self.floating_panel:
            self.floating_panel.deiconify()
            self.floating_panel.update()
        self.update_step_counter_immediate()

    def add_note_during_recording(self):
        dialog = ctk.CTkInputDialog(text="Enter a note:", title="Add Note")
        text = dialog.get_input()
        if text:
            self.recorder.add_note(text)
            self.update_step_counter_immediate()

    def update_step_counter_immediate(self):
        count = len(self.recorder.get_steps())
        self.lbl_steps.configure(text=f"{count} step{'s' if count != 1 else ''}")

    def update_step_counter(self):
        if self.recorder.is_recording:
            self.update_step_counter_immediate()
        self.after(1000, self.update_step_counter)

    def export(self, fmt):
        steps = self.recorder.get_steps()
        if not steps:
            messagebox.showwarning("No Steps", "No steps were captured!")
            return

        tester = self.entry_name.get()
        out_folder = self.entry_path.get()

        if not os.path.isdir(out_folder):
            messagebox.showerror("Invalid Folder",
                                 f"Output folder does not exist:\n{out_folder}")
            return

        timestamp = steps[0].timestamp.replace(":", "-")

        if fmt == "docx":
            filename = os.path.join(out_folder, f"FlowTrace_{timestamp}.docx")
            success, msg = export_docx(steps, filename, tester)
        elif fmt == "pdf":
            filename = os.path.join(out_folder, f"FlowTrace_{timestamp}.pdf")
            success, msg = export_pdf(steps, filename, tester)
        elif fmt == "py":
            filename = os.path.join(out_folder, f"FlowTrace_Script_{timestamp}.py")
            success, msg = export_pyautogui(steps, filename)
        elif fmt == "playwright":
            filename = os.path.join(out_folder, f"FlowTrace_Playwright_{timestamp}.py")
            success, msg = export_playwright(steps, filename)
        elif fmt == "html":
            filename = os.path.join(out_folder, f"FlowTrace_{timestamp}.html")
            success, msg = export_html(steps, filename, tester)
        else:
            messagebox.showerror("Export Failed", f"Unknown export format: {fmt}")
            return

        if success:
            messagebox.showinfo("Exported", f"Saved to:\n{filename}")
        else:
            messagebox.showerror("Export Failed", msg)

    def launch_codegen(self):
        url = self.entry_url.get()
        if not url:
            messagebox.showwarning("Missing URL", "Please enter a URL first!")
            return
        try:
            creationflags = 0x08000000 if sys.platform == "win32" else 0
            if getattr(sys, 'frozen', False):
                cmd = [sys.executable, "--codegen", url]
            else:
                main_py = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
                cmd = [sys.executable, main_py, "--codegen", url]
            subprocess.Popen(cmd, creationflags=creationflags)
            self._set_status("Codegen launched", ACCENT_AMBER, ACCENT_AMBER)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Codegen: {e}")

    def _open_prompt_library(self):
        PromptLibraryWindow(self)
