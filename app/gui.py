"""Tkinter user interface for MM SimpleTools DokumentenSortierer Pro."""

import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageTk
except ImportError:  # pragma: no cover - fallback for minimal Python installs
    Image = None
    ImageTk = None

from app.pdf_tools import InvalidPdfError, NotEnoughPdfFilesError, merge_pdfs, validate_pdf_file
from app.undo_manager import UndoManager


APP_NAME = "MM SimpleTools FileRenamer"
APP_VERSION = "2.0"
APP_EDITION = "Kostenlose Version"
UPGRADE_PRODUCT = "MM SimpleTools DokumentenSortierer Pro"
HEADER_LOGO_SIZE = 120

PRIMARY_GREEN = "#2e7d32"
PRIMARY_BLUE = "#1565c0"
AMBER = "#e67e00"
NAVY = "#1a3a6e"
PAGE_BG = "#f4f6f8"
WHITE = "#ffffff"
TEXT = "#1f2933"
MUTED = "#6b7280"
BORDER = "#d9dee5"
LIGHT_GREEN = "#e8f5e9"
LIGHT_AMBER = "#fff7df"
DISABLED_TEXT = "#747b84"

LOCKED_FEATURES = [
    ("PDF-Seiten extrahieren", "doc", False),
    ("Rechnungen automatisch einsortieren", "bill", False),
    ("Dokumente automatisch nach Typ sortieren", "folder", False),
    ("Briefe automatisch einsortieren", "mail", False),
    ("Dokumente automatisch nach Datum sortieren", "date", False),
    ("Kontoauszüge automatisch einsortieren", "bank", False),
    ("Dokumente automatisch nach Name sortieren", "name", False),
    ("Inkasso-Dokumente automatisch einsortieren", "legal", False),
    ("Umbenannte Dateien automatisch\nals PDF konvertieren (soweit möglich)", "pdf", True),
    ("Verträge automatisch einsortieren", "contract", False),
    ("Undo-Funktion für Dateiaktionen", "undo", True),
]


def resource_path(relative_path):
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return str(base_path / relative_path)


def draw_rounded_rectangle(canvas, x1, y1, x2, y2, radius, **kwargs):
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def collect_file_rename_preview(folder, prefix, start_number):
    files = [
        file for file in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, file))
    ]

    if not files:
        return []

    files.sort()
    preview_items = []
    reserved_paths = set()
    number = start_number

    for file in files:
        old_path = os.path.join(folder, file)
        file_extension = os.path.splitext(file)[1]
        new_filename = f"{prefix}{number:03d}{file_extension}"
        new_path = os.path.join(folder, new_filename)

        while os.path.exists(new_path) or new_path in reserved_paths:
            number += 1
            new_filename = f"{prefix}{number:03d}{file_extension}"
            new_path = os.path.join(folder, new_filename)

        preview_items.append(
            {
                "old_path": old_path,
                "new_path": new_path,
                "old_name": file,
                "new_name": new_filename,
            }
        )
        reserved_paths.add(new_path)
        number += 1

    return preview_items


class DokumentenSortiererProApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} V{APP_VERSION} - {APP_EDITION}")
        self.window_width = 1480
        self.window_height = 900
        self.root.minsize(1100, 680)
        self.root.resizable(True, True)
        self.root.configure(bg=PAGE_BG)
        self.window_icon_photo = None
        self.set_window_icon()

        self.folder_path = tk.StringVar()
        self.prefix = tk.StringVar(value="IMG_")
        self.start_number = tk.StringVar(value="1")
        self.undo_manager = UndoManager()

        self.build_menu()
        self.build_ui()
        self.setup_keyboard_scrolling()
        self.center_window()
        self.maximize_window()

    def set_window_icon(self):
        icon_paths = [
            Path(resource_path(Path("app") / "icon.ico")),
            Path(__file__).resolve().parent / "icon.ico",
            Path.cwd() / "app" / "icon.ico",
        ]

        for icon_path in icon_paths:
            if not icon_path.exists():
                continue

            icon_was_set = False

            try:
                self.root.iconbitmap(default=str(icon_path))
                self.root.wm_iconbitmap(str(icon_path))
                icon_was_set = True
            except tk.TclError:
                pass

            if Image is not None and ImageTk is not None:
                try:
                    icon_image = self.load_ico_image(icon_path, max_size=32)
                    self.window_icon_photo = ImageTk.PhotoImage(icon_image)
                    self.root.iconphoto(True, self.window_icon_photo)
                    icon_was_set = True
                except Exception:
                    pass

            if icon_was_set:
                return

    def center_window(self):
        self.root.update_idletasks()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = min(self.window_width, max(screen_width - 40, 1100))
        window_height = min(self.window_height, max(screen_height - 90, 680))
        x_position = max((screen_width - window_width) // 2, 0)
        y_position = max((screen_height - window_height) // 2, 0)

        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    def maximize_window(self):
        self.root.update_idletasks()

        try:
            self.root.state("zoomed")
        except tk.TclError:
            self.root.attributes("-zoomed", True)

    def load_ico_image(self, icon_path, max_size):
        image = Image.open(icon_path)

        if hasattr(image, "ico"):
            sizes = sorted(image.ico.sizes(), key=lambda size: size[0] * size[1], reverse=True)
            if sizes:
                image = image.ico.getimage(sizes[0])

        image = image.convert("RGBA")
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        return image

    def setup_keyboard_scrolling(self):
        key_actions = {
            "Up": lambda canvas: canvas.yview_scroll(-1, "units"),
            "Down": lambda canvas: canvas.yview_scroll(1, "units"),
            "Prior": lambda canvas: canvas.yview_scroll(-1, "pages"),
            "Next": lambda canvas: canvas.yview_scroll(1, "pages"),
            "Home": lambda canvas: canvas.yview_moveto(0),
            "End": lambda canvas: canvas.yview_moveto(1),
        }

        def find_canvas_under_pointer():
            pointer_x = self.root.winfo_pointerx()
            pointer_y = self.root.winfo_pointery()
            widget = self.root.winfo_containing(pointer_x, pointer_y)

            while widget is not None:
                canvas = getattr(widget, "_mm_scroll_canvas", None)
                if canvas is not None:
                    return canvas
                widget = widget.master

            return None

        def handle_key_scroll(event):
            action = key_actions.get(event.keysym)

            if action is None:
                return None

            canvas = find_canvas_under_pointer()

            if canvas is None:
                return None

            action(canvas)
            return "break"

        for key in key_actions:
            self.root.bind_all(f"<{key}>", handle_key_scroll, add="+")

    def build_ui(self):
        self.build_header()
        self.build_main_body()
        self.build_footer()

    def build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Ordner auswählen", command=self.select_folder)
        file_menu.add_command(label="Dateien umbenennen", command=self.rename_files)
        file_menu.add_command(label="PDFs zusammenführen", command=self.merge_selected_pdfs)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.root.destroy)
        menubar.add_cascade(label="Datei", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=False)
        edit_menu.add_command(label="Letzte Umbenennung rückgängig", command=self.undo_last_rename)
        menubar.add_cascade(label="Bearbeiten", menu=edit_menu)

        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_command(label="Fenster zurücksetzen", command=self.reset_window)
        view_menu.add_command(label="Alles sichtbar anzeigen", command=self.show_all_content)
        menubar.add_cascade(label="Ansicht", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Über MM SimpleTools", command=self.show_about)
        help_menu.add_command(label="Website öffnen", command=self.open_website)
        menubar.add_cascade(label="Hilfe", menu=help_menu)

        self.root.config(menu=menubar)

    def build_header(self):
        header = tk.Frame(self.root, bg=WHITE)
        header.pack(fill="x")
        header.columnconfigure(0, weight=1)

        header_content = tk.Frame(header, bg=WHITE)
        header_content.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 16))
        header_content.columnconfigure(0, weight=0)
        header_content.columnconfigure(1, weight=1)

        logo = self.create_logo_widget(header_content)
        logo.grid(row=0, column=0, sticky="nw", padx=(0, 18), pady=(2, 0))

        text_column = tk.Frame(header_content, bg=WHITE)
        text_column.grid(row=0, column=1, sticky="ew")
        text_column.columnconfigure(0, weight=1)

        title_label = tk.Label(
            text_column,
            text=f"{APP_NAME} V{APP_VERSION}",
            bg=WHITE,
            fg=TEXT,
            font=("Arial", 26, "bold"),
            anchor="w",
            justify="left",
        )
        title_label.grid(row=0, column=0, sticky="ew")

        edition_label = tk.Label(
            text_column,
            text=APP_EDITION,
            bg=WHITE,
            fg=PRIMARY_GREEN,
            font=("Arial", 20, "bold"),
            anchor="w",
            justify="left",
        )
        edition_label.grid(row=1, column=0, sticky="ew", pady=(1, 4))

        description_label = tk.Label(
            text_column,
            text=(
                "FileRenamer V2.0 ist die kostenlose Einstiegsversion. "
                f"{UPGRADE_PRODUCT} ist das kostenpflichtige Hauptprodukt mit erweiterten Dokumenten- und PDF-Funktionen."
            ),
            bg=WHITE,
            fg="#111827",
            font=("Arial", 12),
            anchor="w",
            justify="left",
        )
        description_label.grid(row=2, column=0, sticky="ew")

        status_box = tk.Frame(text_column, bg=WHITE, highlightbackground=PRIMARY_GREEN, highlightthickness=1)
        status_box.grid(row=3, column=0, sticky="ew", pady=(14, 0), ipadx=10, ipady=6)
        status_box.columnconfigure(1, weight=1)

        shield = tk.Canvas(status_box, width=70, height=70, bg=WHITE, bd=0, highlightthickness=0)
        shield.grid(row=0, column=0, rowspan=3, sticky="n", padx=(16, 18), pady=10)
        shield.create_oval(4, 4, 66, 66, outline=PRIMARY_GREEN, width=3)
        shield.create_oval(23, 18, 47, 48, fill=PRIMARY_GREEN, outline=PRIMARY_GREEN)
        shield.create_text(35, 36, text="✓", fill=WHITE, font=("Arial", 20, "bold"))

        tk.Label(
            status_box,
            text="KOSTENLOSE VERSION",
            bg=WHITE,
            fg=PRIMARY_GREEN,
            font=("Arial", 18, "bold"),
            anchor="w",
            justify="left",
        ).grid(row=0, column=1, sticky="ew", padx=(0, 18), pady=(8, 0))
        tk.Label(
            status_box,
            text="FileRenamer V2.0 ist die kostenlose Einstiegsversion.",
            bg=WHITE,
            fg=PRIMARY_GREEN,
            font=("Arial", 12, "bold"),
            anchor="w",
            justify="left",
        ).grid(row=1, column=1, sticky="ew", padx=(0, 18), pady=(4, 0))
        status_description_label = tk.Label(
            status_box,
            text=(
                "MM SimpleTools DokumentenSortierer Pro ist das kostenpflichtige "
                "Hauptprodukt mit erweiterten Dokumenten- und PDF-Funktionen."
            ),
            bg=WHITE,
            fg=PRIMARY_GREEN,
            font=("Arial", 12),
            anchor="w",
            justify="left",
        )
        status_description_label.grid(row=2, column=1, sticky="ew", padx=(0, 18), pady=(0, 8))

        def update_header_wrap(event=None):
            available_width = max(text_column.winfo_width() - 4, 220)
            title_label.configure(wraplength=available_width)
            edition_label.configure(wraplength=available_width)
            description_label.configure(wraplength=available_width)
            status_description_label.configure(wraplength=max(available_width - 120, 220))

        text_column.bind("<Configure>", update_header_wrap)
        self.root.after_idle(update_header_wrap)

    def create_logo_widget(self, parent):
        logo_paths = [
            Path(resource_path(Path("app") / "assets" / "MM_SimpleTools_Header.png")),
            Path(__file__).resolve().parent / "assets" / "MM_SimpleTools_Header.png",
            Path.cwd() / "app" / "assets" / "MM_SimpleTools_Header.png",
            Path(resource_path(Path("app") / "assets" / "MM_SimpleTools_TikTok_Logo.png")),
            Path(__file__).resolve().parent / "assets" / "MM_SimpleTools_TikTok_Logo.png",
            Path.cwd() / "app" / "assets" / "MM_SimpleTools_TikTok_Logo.png",
        ]

        for logo_path in logo_paths:
            if not logo_path.exists():
                continue

            try:
                if Image is not None and ImageTk is not None:
                    logo_image = Image.open(logo_path).convert("RGBA")
                    logo_image.thumbnail((HEADER_LOGO_SIZE, HEADER_LOGO_SIZE), Image.Resampling.LANCZOS)
                    self.logo_photo = ImageTk.PhotoImage(logo_image)
                else:
                    logo_photo = tk.PhotoImage(file=str(logo_path))
                    scale = max(
                        (logo_photo.width() + HEADER_LOGO_SIZE - 1) // HEADER_LOGO_SIZE,
                        (logo_photo.height() + HEADER_LOGO_SIZE - 1) // HEADER_LOGO_SIZE,
                        1,
                    )
                    self.logo_photo = logo_photo.subsample(scale, scale)

                return tk.Label(parent, image=self.logo_photo, bg=WHITE, width=HEADER_LOGO_SIZE, height=HEADER_LOGO_SIZE)
            except Exception:
                continue

        logo = tk.Canvas(parent, width=96, height=96, bg=WHITE, bd=0, highlightthickness=0)
        draw_rounded_rectangle(logo, 0, 0, 96, 96, 12, fill=NAVY, outline=NAVY)
        logo.create_text(48, 34, text="MM", fill=WHITE, font=("Arial", 23, "bold"))
        logo.create_text(48, 60, text="SIMPLE", fill=WHITE, font=("Arial", 9, "bold"))
        logo.create_text(48, 75, text="TOOLS", fill=WHITE, font=("Arial", 9, "bold"))
        return logo

    def build_main_body(self):
        body_container = tk.Frame(self.root, bg=PAGE_BG)
        body_container.pack(fill="both", expand=True)
        body_container.columnconfigure(0, weight=49, minsize=560)
        body_container.columnconfigure(1, weight=51, minsize=560)
        body_container.rowconfigure(0, weight=1)

        left_host, left_content = self.create_vertical_scrollable_pane(
            body_container,
            bg=WHITE,
            border=True,
        )
        left_host.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.left_canvas = left_host.canvas

        right_host, right_content = self.create_vertical_scrollable_pane(body_container, bg=PAGE_BG)
        right_host.grid(row=0, column=1, sticky="nsew")
        self.right_canvas = right_host.canvas

        self.build_left_pane(left_content)
        self.build_right_pane(right_content)

    def create_vertical_scrollable_pane(self, parent, width=None, bg=PAGE_BG, border=False):
        host = tk.Frame(
            parent,
            bg=bg,
            highlightbackground=BORDER if border else bg,
            highlightthickness=1 if border else 0,
        )
        if width is not None:
            host.configure(width=width)
            host.grid_propagate(False)
        host.columnconfigure(0, weight=1)
        host.rowconfigure(0, weight=1)

        canvas = tk.Canvas(host, bg=bg, bd=0, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        canvas._mm_scroll_canvas = canvas

        scrollbar_host = tk.Frame(host, bg=bg)
        scrollbar_host.grid(row=0, column=1, sticky="ns")
        scrollbar_host.rowconfigure(0, weight=1)

        vertical_scrollbar = tk.Scrollbar(
            scrollbar_host,
            orient="vertical",
            command=canvas.yview,
            width=18,
            bd=0,
            relief="flat",
            bg="#cfd6df",
            activebackground="#aeb8c4",
            troughcolor=bg,
        )
        vertical_scrollbar.grid(row=0, column=0, sticky="ns", padx=(2, 2))

        canvas.configure(
            yscrollcommand=vertical_scrollbar.set,
        )

        content = tk.Frame(canvas, bg=bg)
        content._mm_scroll_canvas = canvas
        window = canvas.create_window((0, 0), window=content, anchor="nw")

        def update_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfigure(window, width=canvas.winfo_width())

        def scroll_vertical(event):
            if getattr(event, "num", None) == 4:
                canvas.yview_scroll(-1, "units")
                return "break"

            if getattr(event, "num", None) == 5:
                canvas.yview_scroll(1, "units")
                return "break"

            delta = getattr(event, "delta", 0)
            if delta:
                units = int(-1 * (delta / 120))
                if units == 0:
                    units = -1 if delta > 0 else 1
                canvas.yview_scroll(units, "units")
                return "break"

            return None

        def bind_mousewheel(widget):
            widget._mm_scroll_canvas = canvas

            if not getattr(widget, "_mm_mousewheel_bound", False):
                widget.bind("<MouseWheel>", scroll_vertical, add="+")
                widget.bind("<Button-4>", scroll_vertical, add="+")
                widget.bind("<Button-5>", scroll_vertical, add="+")
                widget._mm_mousewheel_bound = True

            for child in widget.winfo_children():
                bind_mousewheel(child)

        def bind_content_mousewheel(event=None):
            bind_mousewheel(host)

        content.bind("<Configure>", update_scroll_region)
        content.bind("<Configure>", bind_content_mousewheel, add="+")
        canvas.bind("<Configure>", update_scroll_region)
        bind_mousewheel(host)
        host.canvas = canvas
        host._mm_scroll_canvas = canvas

        return host, content

    def build_left_pane(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        left = tk.Frame(parent, bg=WHITE)
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)
        left.rowconfigure(3, weight=1)

        tk.Label(
            left,
            text="KOSTENLOSE FUNKTIONEN",
            bg=WHITE,
            fg=PRIMARY_GREEN,
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=28, pady=(18, 12))

        rename_card = self.create_panel_card(left)
        rename_card.grid(row=1, column=0, sticky="ew", padx=28, pady=(0, 14))
        rename_card.columnconfigure(0, weight=1)
        rename_card.columnconfigure(1, weight=0)

        self.create_card_header(rename_card, "rename", "Dateien sauber umbenennen").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 16)
        )

        tk.Label(rename_card, text="Ordner:", bg=WHITE, fg=TEXT, font=("Arial", 9, "bold")).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        tk.Entry(rename_card, textvariable=self.folder_path, state="readonly", font=("Arial", 11)).grid(
            row=2, column=0, sticky="ew", padx=(0, 12), ipady=8
        )
        self.create_button(
            rename_card,
            "📁  Auswählen",
            self.select_folder,
            bg=WHITE,
            fg=TEXT,
            border=BORDER,
        ).grid(row=2, column=1, sticky="ew")

        tk.Label(rename_card, text="Dateiname / Prefix:", bg=WHITE, fg=TEXT, font=("Arial", 9)).grid(
            row=3, column=0, sticky="w", pady=(12, 4)
        )
        tk.Label(rename_card, text="Startnummer:", bg=WHITE, fg=TEXT, font=("Arial", 9)).grid(
            row=3, column=1, sticky="w", pady=(12, 4)
        )
        tk.Entry(rename_card, textvariable=self.prefix, font=("Arial", 11)).grid(
            row=4, column=0, sticky="ew", padx=(0, 12), ipady=8
        )
        tk.Entry(rename_card, textvariable=self.start_number, font=("Arial", 11), width=22).grid(
            row=4, column=1, sticky="ew", ipady=8
        )

        self.create_button(
            rename_card,
            "Preview",
            self.show_preview,
            bg=WHITE,
            fg=PRIMARY_BLUE,
            border=PRIMARY_BLUE,
            bold=True,
        ).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(14, 4))

        tk.Label(
            rename_card,
            text="Ausgewählte Dateien als Vorschau anzeigen",
            bg=WHITE,
            fg=MUTED,
            font=("Arial", 9),
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.create_button(
            rename_card,
            "✎  Dateien umbenennen",
            self.rename_files,
            bg=PRIMARY_GREEN,
            fg=WHITE,
            border=PRIMARY_GREEN,
            bold=True,
        ).grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        self.create_button(
            rename_card,
            "↩  Letzte Umbenennung rückgängig",
            self.undo_last_rename,
            bg=WHITE,
            fg=TEXT,
            border=BORDER,
        ).grid(row=8, column=0, columnspan=2, sticky="ew")

        pdf_card = self.create_panel_card(left)
        pdf_card.grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 24))
        pdf_card.columnconfigure(0, weight=1)

        self.create_card_header(pdf_card, "pdf-blue", "PDFs zusammenführen").grid(row=0, column=0, sticky="w", pady=(0, 14))
        self.create_button(
            pdf_card,
            "▧  PDFs zusammenführen",
            self.merge_selected_pdfs,
            bg=PRIMARY_BLUE,
            fg=WHITE,
            border=PRIMARY_BLUE,
            bold=True,
        ).grid(row=1, column=0, sticky="ew")

        info_bar = tk.Frame(left, bg=LIGHT_GREEN, highlightbackground=PRIMARY_GREEN, highlightthickness=1)
        info_bar.grid(row=4, column=0, sticky="sew", padx=28, pady=(0, 20))
        shield_icon = tk.Canvas(info_bar, width=34, height=34, bg=LIGHT_GREEN, bd=0, highlightthickness=0)
        shield_icon.grid(row=0, column=0, rowspan=2, sticky="n", padx=(12, 10), pady=11)
        shield_icon.create_polygon(17, 2, 29, 8, 27, 24, 17, 32, 7, 24, 5, 8, fill=LIGHT_GREEN, outline=PRIMARY_GREEN, width=2)
        shield_icon.create_text(17, 18, text="✓", fill=PRIMARY_GREEN, font=("Arial", 12, "bold"))
        tk.Label(
            info_bar,
            text="LOKALE VERARBEITUNG OHNE CLOUD",
            bg=LIGHT_GREEN,
            fg=PRIMARY_GREEN,
            font=("Arial", 10, "bold"),
        ).grid(row=0, column=1, sticky="w", padx=(0, 10), pady=(10, 0))
        tk.Label(
            info_bar,
            text="Keine Datenübertragung. Ihre Dateien bleiben auf Ihrem Gerät.",
            bg=LIGHT_GREEN,
            fg=TEXT,
            font=("Arial", 10),
            wraplength=460,
            justify="left",
        ).grid(row=1, column=1, sticky="w", padx=(0, 10), pady=(2, 10))

    def build_right_pane(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        right = tk.Frame(parent, bg=PAGE_BG)
        right.grid(row=0, column=0, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        upgrade_title = tk.Label(
            right,
            text=f"SICHTBARE, GESPERRTE UPGRADE-FUNKTIONEN – {UPGRADE_PRODUCT.upper()}",
            bg=PAGE_BG,
            fg=AMBER,
            font=("Arial", 12, "bold"),
            anchor="w",
            justify="left",
        )
        upgrade_title.grid(row=0, column=0, sticky="ew", padx=16, pady=(18, 10))

        banner = tk.Frame(right, bg=LIGHT_AMBER, highlightbackground=AMBER, highlightthickness=1)
        banner.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))
        banner.columnconfigure(1, weight=1)
        lock_canvas = tk.Canvas(banner, width=58, height=48, bg=LIGHT_AMBER, bd=0, highlightthickness=0)
        lock_canvas.grid(row=0, column=0, sticky="n", padx=(16, 12), pady=14)
        lock_canvas.create_arc(11, 6, 35, 30, start=0, extent=180, outline=AMBER, width=3, style="arc")
        lock_canvas.create_rectangle(9, 22, 37, 42, fill=AMBER, outline=AMBER)
        lock_canvas.create_oval(34, 25, 52, 43, fill="#374151", outline="#374151")
        lock_canvas.create_text(43, 34, text="+", fill=WHITE, font=("Arial", 10, "bold"))
        banner_label = tk.Label(
            banner,
            text=(
                f"{UPGRADE_PRODUCT} ist das kostenpflichtige Upgrade für automatische "
                "Dokumenten-Sortierung, erweiterte PDF-Funktionen und Dateiaktionen."
            ),
            bg=LIGHT_AMBER,
            fg="#8a4b00",
            font=("Arial", 12, "bold"),
            anchor="w",
            justify="left",
        )
        banner_label.grid(row=0, column=1, sticky="ew", padx=(0, 20), pady=16)

        grid = tk.Frame(right, bg=PAGE_BG)
        grid.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 10))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        feature_positions = [
            (0, 0, 1),
            (0, 1, 1),
            (1, 0, 1),
            (1, 1, 1),
            (2, 0, 1),
            (2, 1, 1),
            (3, 0, 1),
            (3, 1, 1),
            (4, 0, 1),
            (4, 1, 1),
            (5, 0, 2),
        ]

        for feature, position in zip(LOCKED_FEATURES, feature_positions):
            row, column, span = position
            grid.rowconfigure(row, weight=1)
            self.create_locked_feature_card(grid, feature).grid(
                row=row,
                column=column,
                columnspan=span,
                sticky="nsew",
                padx=7,
                pady=6,
            )

        def update_right_wrap(event=None):
            available_width = max(right.winfo_width() - 48, 260)
            upgrade_title.configure(wraplength=available_width)
            banner_label.configure(wraplength=max(available_width - 80, 220))

        right.bind("<Configure>", update_right_wrap)
        self.root.after_idle(update_right_wrap)

    def build_footer(self):
        footer = tk.Frame(self.root, bg=WHITE, height=62, highlightbackground=BORDER, highlightthickness=1)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        footer.columnconfigure(1, weight=1)

        left_buttons = tk.Frame(footer, bg=WHITE)
        left_buttons.grid(row=0, column=0, sticky="w", padx=20, pady=12)
        self.create_footer_button(left_buttons, "ℹ️ Über MM SimpleTools", self.show_about).pack(side="left", padx=(0, 8))
        self.create_footer_button(left_buttons, "🌐 Website öffnen", self.open_website).pack(side="left")

        right_buttons = tk.Frame(footer, bg=WHITE)
        right_buttons.grid(row=0, column=2, sticky="e", padx=20, pady=12)
        self.create_footer_button(
            right_buttons,
            "🛒 Upgrade sichern",
            self.show_upgrade,
            fg=PRIMARY_BLUE,
            border=PRIMARY_BLUE,
        ).pack(side="left", padx=(0, 8))
        self.create_footer_button(right_buttons, "❓ Hilfe", self.show_help).pack(side="left", padx=(0, 8))
        self.create_footer_button(
            right_buttons,
            "✕ Beenden",
            self.root.destroy,
            fg="#b3261e",
            border="#b3261e",
        ).pack(side="left")

    def create_panel_card(self, parent):
        card = tk.Frame(parent, bg=WHITE, highlightbackground=BORDER, highlightthickness=1, padx=18, pady=18)
        return card

    def create_card_header(self, parent, icon, text):
        header = tk.Frame(parent, bg=WHITE)
        icon_canvas = tk.Canvas(header, width=28, height=28, bg=WHITE, bd=0, highlightthickness=0)
        icon_canvas.pack(side="left", padx=(0, 9))
        if icon == "rename":
            icon_canvas.create_text(14, 14, text="⟳", fill="#0ea5b7", font=("Arial", 17, "bold"))
            icon_canvas.create_text(20, 20, text="•", fill=PRIMARY_BLUE, font=("Arial", 10, "bold"))
        elif icon == "pdf-blue":
            icon_canvas.create_rectangle(7, 3, 20, 25, fill=PRIMARY_BLUE, outline=PRIMARY_BLUE)
            icon_canvas.create_polygon(20, 3, 25, 8, 20, 8, fill="#cfe8ff", outline="#cfe8ff")
            icon_canvas.create_line(10, 12, 18, 12, fill=WHITE, width=2)
            icon_canvas.create_line(10, 16, 18, 16, fill=WHITE, width=2)
        else:
            icon_canvas.create_text(14, 14, text=icon, fill=TEXT, font=("Arial", 15))
        tk.Label(header, text=text, bg=WHITE, fg=TEXT, font=("Arial", 12, "bold")).pack(side="left")
        return header

    def create_button(self, parent, text, command, bg, fg, border, bold=False):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=bg,
            activeforeground=fg,
            relief="solid",
            bd=1,
            highlightbackground=border,
            font=("Arial", 11, "bold" if bold else "normal"),
            padx=10,
            pady=9,
            cursor="hand2",
        )

    def create_footer_button(self, parent, text, command, fg=TEXT, border=BORDER):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=WHITE,
            fg=fg,
            relief="solid",
            bd=1,
            highlightbackground=border,
            font=("Arial", 9),
            padx=12,
            pady=6,
            cursor="hand2",
        )

    def create_locked_feature_card(self, parent, feature):
        title, icon, is_wide = feature
        card_bg = "#fbfcfd"
        card = tk.Frame(parent, bg=card_bg, highlightbackground="#d6dde7", highlightthickness=1, padx=16, pady=12)
        card.columnconfigure(1, weight=1)

        icon_canvas = tk.Canvas(card, width=66, height=60, bg=card_bg, bd=0, highlightthickness=0)
        icon_canvas.grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 14), pady=(1, 0))
        self.draw_locked_icon(icon_canvas, icon)

        title_label = tk.Label(
            card,
            text=title,
            bg=card_bg,
            fg=TEXT,
            font=("Arial", 10, "bold"),
            anchor="w",
            justify="left",
        )
        title_label.grid(row=0, column=1, sticky="ew")

        availability_label = tk.Label(
            card,
            text=f"Verfügbar in {UPGRADE_PRODUCT}",
            bg=card_bg,
            fg="#a95700",
            font=("Arial", 8),
            anchor="w",
            justify="left",
        )
        availability_label.grid(row=1, column=1, sticky="ew", pady=(5, 0))

        def update_card_wrap(event=None):
            wrap_length = max(card.winfo_width() - icon_canvas.winfo_width() - 62, 150)
            title_label.configure(wraplength=wrap_length)
            availability_label.configure(wraplength=wrap_length)

        card.bind("<Configure>", update_card_wrap)
        self.root.after_idle(update_card_wrap)

        return card

    def draw_locked_icon(self, canvas, icon_kind):
        canvas.create_rectangle(5, 4, 53, 55, fill="#eef1f5", outline="#eef1f5")
        color = "#90979f"

        if icon_kind in {"doc", "bill", "pdf", "undo"}:
            canvas.create_rectangle(18, 9, 42, 45, fill="#f8f9fa", outline=color, width=2)
            canvas.create_polygon(42, 9, 51, 18, 42, 18, fill="#e4e7eb", outline=color)
            canvas.create_line(23, 25, 39, 25, fill=color, width=2)
            canvas.create_line(23, 31, 39, 31, fill=color, width=2)
            if icon_kind == "undo":
                canvas.create_text(31, 32, text="↩", fill=color, font=("Arial", 16, "bold"))
        elif icon_kind == "folder":
            canvas.create_polygon(11, 23, 25, 23, 29, 28, 51, 28, 51, 47, 11, 47, fill="#d7dbe0", outline=color)
        elif icon_kind == "mail":
            canvas.create_rectangle(12, 16, 51, 44, fill="#d7dbe0", outline=color)
            canvas.create_line(12, 16, 32, 33, 51, 16, fill=color, width=2)
        elif icon_kind == "date":
            canvas.create_rectangle(13, 12, 51, 46, fill="#f8f9fa", outline=color, width=2)
            canvas.create_line(13, 22, 51, 22, fill=color, width=2)
            for x in (22, 33, 44):
                canvas.create_oval(x - 2, 31, x + 2, 35, fill=color, outline=color)
        elif icon_kind == "bank":
            canvas.create_polygon(11, 22, 32, 10, 53, 22, fill=color, outline=color)
            canvas.create_rectangle(15, 43, 49, 47, fill=color, outline=color)
            for x in (20, 32, 44):
                canvas.create_rectangle(x - 2, 25, x + 2, 43, fill=color, outline=color)
        elif icon_kind == "name":
            canvas.create_text(23, 25, text="A", fill=color, font=("Arial", 17, "bold"))
            canvas.create_text(40, 25, text="I", fill=color, font=("Arial", 17, "italic"))
            canvas.create_text(27, 41, text="7", fill=color, font=("Arial", 13, "italic"))
        elif icon_kind == "legal":
            canvas.create_line(32, 13, 32, 43, fill=color, width=3)
            canvas.create_line(18, 20, 48, 20, fill=color, width=2)
            canvas.create_text(20, 36, text="⚖", fill=color, font=("Arial", 20))
        elif icon_kind == "contract":
            canvas.create_text(31, 30, text="🤝", fill=color, font=("Arial", 20))

        canvas.create_rectangle(46, 39, 62, 57, fill="#4b5563", outline="#4b5563")
        canvas.create_arc(48, 31, 60, 47, start=0, extent=180, outline="#4b5563", width=2, style="arc")
        canvas.create_text(54, 49, text="●", fill=WHITE, font=("Arial", 5))

    def show_about(self):
        messagebox.showinfo(
            "Über MM SimpleTools",
            "MM SimpleTools FileRenamer V2.0\nKostenlose Version",
        )

    def open_website(self):
        messagebox.showinfo("Website öffnen", "Hier kann später die MM SimpleTools Website geöffnet werden.")

    def show_upgrade(self):
        messagebox.showinfo(
            "Upgrade sichern",
            f"Verfügbar in {UPGRADE_PRODUCT}.",
        )

    def show_help(self):
        messagebox.showinfo(
            "Hilfe",
            "Wählen Sie einen Ordner aus, setzen Sie Prefix und Startnummer, und starten Sie die Umbenennung.",
        )

    def reset_window(self):
        self.left_canvas.yview_moveto(0)
        self.right_canvas.yview_moveto(0)
        self.center_window()

    def show_all_content(self):
        self.root.state("zoomed")
        self.left_canvas.yview_moveto(0)
        self.right_canvas.yview_moveto(0)

    def select_folder(self):
        selected_folder = filedialog.askdirectory()

        if selected_folder:
            self.folder_path.set(selected_folder)

    def get_validated_rename_inputs(self):
        folder = self.folder_path.get()
        prefix = self.prefix.get().strip()
        start_number_text = self.start_number.get().strip()

        if not folder:
            messagebox.showerror("Fehler", "Bitte zuerst einen Ordner auswählen.")
            return None

        if not prefix:
            messagebox.showerror("Fehler", "Bitte einen Dateinamen / Prefix eingeben.")
            return None

        if not start_number_text.isdigit():
            messagebox.showerror("Fehler", "Die Startnummer muss eine Zahl sein.")
            return None

        return folder, prefix, int(start_number_text)

    def show_preview(self):
        validated_inputs = self.get_validated_rename_inputs()

        if validated_inputs is None:
            return

        folder, prefix, start_number = validated_inputs

        try:
            preview_items = collect_file_rename_preview(folder, prefix, start_number)

            if not preview_items:
                messagebox.showinfo("Hinweis", "Im ausgewählten Ordner wurden keine Dateien gefunden.")
                return

            self.open_preview_window(preview_items)

        except PermissionError:
            messagebox.showerror(
                "Fehler",
                "Zugriff verweigert. Bitte prüfen, ob Dateien geöffnet sind oder Administratorrechte benötigt werden."
            )

        except Exception as error:
            messagebox.showerror(
                "Fehler",
                f"Die Vorschau konnte nicht erstellt werden:\n{error}"
            )

    def open_preview_window(self, preview_items):
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Preview - Vorschau")
        preview_window.geometry("860x520")
        preview_window.minsize(620, 360)
        preview_window.transient(self.root)

        tk.Label(
            preview_window,
            text="Original-Dateiname \u2192 geplanter neuer Dateiname",
            font=("Arial", 12, "bold"),
            anchor="w",
        ).pack(fill="x", padx=14, pady=(14, 8))

        table_frame = tk.Frame(preview_window)
        table_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        table = ttk.Treeview(
            table_frame,
            columns=("original", "arrow", "planned"),
            show="headings",
            selectmode="browse",
        )
        table.heading("original", text="Original-Dateiname")
        table.heading("arrow", text="")
        table.heading("planned", text="Geplanter neuer Dateiname")
        table.column("original", width=360, minwidth=180, anchor="w", stretch=True)
        table.column("arrow", width=36, anchor="center", stretch=False)
        table.column("planned", width=360, minwidth=180, anchor="w", stretch=True)

        vertical_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=vertical_scrollbar.set)

        table.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")

        for item in preview_items:
            table.insert("", "end", values=(item["old_name"], "\u2192", item["new_name"]))

        tk.Label(
            preview_window,
            text="Vorschau lokal erstellt. Es wurden keine Dateien verändert.",
            font=("Arial", 9),
            fg=MUTED,
            anchor="w",
        ).pack(fill="x", padx=14, pady=(0, 10))

    def rename_files(self):
        validated_inputs = self.get_validated_rename_inputs()

        if validated_inputs is None:
            return

        folder, prefix, start_number = validated_inputs

        try:
            preview_items = collect_file_rename_preview(folder, prefix, start_number)

            if not preview_items:
                messagebox.showinfo("Hinweis", "Im ausgewählten Ordner wurden keine Dateien gefunden.")
                return

            renamed_count = 0
            rename_operations = []

            for item in preview_items:
                os.rename(item["old_path"], item["new_path"])
                rename_operations.append(
                    {
                        "old_path": item["old_path"],
                        "new_path": item["new_path"],
                    }
                )

                renamed_count += 1

            self.undo_manager.record_rename(folder, rename_operations)

            messagebox.showinfo(
                "Fertig",
                f"{renamed_count} Datei(en) wurden erfolgreich umbenannt."
            )

        except PermissionError:
            messagebox.showerror(
                "Fehler",
                "Zugriff verweigert. Bitte prüfen, ob Dateien geöffnet sind oder Administratorrechte benötigt werden."
            )

        except Exception as error:
            messagebox.showerror(
                "Fehler",
                f"Ein unerwarteter Fehler ist aufgetreten:\n{error}"
            )

    def undo_last_rename(self):
        try:
            restored_count = self.undo_manager.undo_last_rename()
            messagebox.showinfo(
                "Rückgängig",
                f"{restored_count} Datei(en) wurden erfolgreich zurückbenannt."
            )

        except ValueError as error:
            messagebox.showinfo("Hinweis", str(error))

        except (FileNotFoundError, FileExistsError, PermissionError) as error:
            messagebox.showerror(
                "Fehler",
                f"Die letzte Umbenennung konnte nicht rückgängig gemacht werden:\n{error}"
            )

        except Exception as error:
            messagebox.showerror(
                "Fehler",
                f"Ein unerwarteter Fehler ist aufgetreten:\n{error}"
            )

    def merge_selected_pdfs(self):
        input_files = filedialog.askopenfilenames(
            title="PDF-Dateien auswählen",
            filetypes=[("PDF-Dateien", "*.pdf"), ("Alle Dateien", "*.*")]
        )

        if not input_files:
            return

        if len(input_files) == 1:
            try:
                validate_pdf_file(input_files[0])
            except InvalidPdfError as error:
                self.show_invalid_pdf_hint(error.filename)
                return

            messagebox.showwarning(
                "Hinweis",
                "Bitte wählen Sie mindestens zwei PDF-Dateien aus.\n\n"
                "Zum Zusammenführen werden mindestens zwei PDF-Dateien benötigt."
            )
            return

        output_file = filedialog.asksaveasfilename(
            title="Ziel-PDF speichern",
            defaultextension=".pdf",
            filetypes=[("PDF-Dateien", "*.pdf")]
        )

        if not output_file:
            return

        try:
            merge_pdfs(list(input_files), output_file)
            messagebox.showinfo(
                "PDFs zusammenführen",
                "Die PDF-Dateien wurden erfolgreich zusammengeführt."
            )

        except InvalidPdfError as error:
            self.show_invalid_pdf_hint(error.filename)

        except NotEnoughPdfFilesError:
            messagebox.showwarning(
                "Hinweis",
                "Bitte wählen Sie mindestens zwei PDF-Dateien aus.\n\n"
                "Zum Zusammenführen werden mindestens zwei PDF-Dateien benötigt."
            )

        except Exception as error:
            messagebox.showerror(
                "Fehler",
                f"Die PDF-Dateien konnten nicht zusammengeführt werden:\n{error}"
            )

    def show_invalid_pdf_hint(self, filename):
        messagebox.showwarning(
            "Hinweis",
            "Die ausgewählte Datei ist keine gültige PDF-Datei:\n\n"
            f"{filename}\n\n"
            "Bitte wählen Sie eine echte PDF-Datei aus."
        )

    def prepare_extract_pdf_pages(self):
        messagebox.showinfo(
            "PDF-Seiten extrahieren",
            "Diese Funktion ist in der kostenlosen Version gesperrt.\n"
            f"Verfügbar in {UPGRADE_PRODUCT}."
        )


FileRenamerApp = DokumentenSortiererProApp
