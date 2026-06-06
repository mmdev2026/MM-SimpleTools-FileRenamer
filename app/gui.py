"""Tkinter user interface for MM SimpleTools FileRenamer."""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

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
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)


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


class FileRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} V{APP_VERSION} - {APP_EDITION}")
        self.window_width = 1480
        self.window_height = 900
        self.root.minsize(1100, 680)
        self.root.resizable(True, True)
        self.root.configure(bg=PAGE_BG)
        self.set_window_icon()

        self.folder_path = tk.StringVar()
        self.prefix = tk.StringVar(value="IMG_")
        self.start_number = tk.StringVar(value="1")
        self.undo_manager = UndoManager()

        self.build_menu()
        self.build_ui()
        self.center_window()

    def set_window_icon(self):
        icon_paths = [
            resource_path(os.path.join("app", "icon.ico")),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico"),
            os.path.join(os.getcwd(), "app", "icon.ico"),
        ]

        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                try:
                    self.root.iconbitmap(icon_path)
                    return
                except tk.TclError:
                    continue

    def center_window(self):
        self.root.update_idletasks()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = min(self.window_width, max(screen_width - 40, 1100))
        window_height = min(self.window_height, max(screen_height - 90, 680))
        x_position = max((screen_width - window_width) // 2, 0)
        y_position = max((screen_height - window_height) // 2, 0)

        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

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
        header = tk.Frame(self.root, bg=WHITE, height=194)
        header.pack(fill="x")
        header.pack_propagate(False)
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)

        left = tk.Frame(header, bg=WHITE)
        left.grid(row=0, column=0, sticky="nsew", padx=24, pady=(30, 12))
        left.columnconfigure(1, weight=1)

        logo = self.create_logo_widget(left)
        logo.grid(row=0, column=0, rowspan=3, sticky="nw", padx=(0, 14))

        tk.Label(
            left,
            text=f"{APP_NAME} V{APP_VERSION}",
            bg=WHITE,
            fg=TEXT,
            font=("Arial", 29, "bold"),
        ).grid(row=0, column=1, sticky="w")

        tk.Label(
            left,
            text=APP_EDITION,
            bg=WHITE,
            fg=PRIMARY_GREEN,
            font=("Arial", 20, "bold"),
        ).grid(row=1, column=1, sticky="w", pady=(1, 4))

        tk.Label(
            left,
            text=(
                "FileRenamer V2.0 ist die kostenlose Einstiegsversion. "
                f"{UPGRADE_PRODUCT} ist das kostenpflichtige Hauptprodukt mit erweiterten Dokumenten- und PDF-Funktionen."
            ),
            bg=WHITE,
            fg="#111827",
            font=("Arial", 12),
            wraplength=720,
            justify="left",
        ).grid(row=2, column=1, sticky="w")

        status_box = tk.Frame(header, bg=WHITE, highlightbackground=PRIMARY_GREEN, highlightthickness=1)
        status_box.grid(row=0, column=1, sticky="e", padx=24, pady=(42, 20), ipadx=10, ipady=6)
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
        ).grid(row=0, column=1, sticky="w", padx=(0, 18), pady=(8, 0))
        tk.Label(
            status_box,
            text="FileRenamer V2.0 ist die kostenlose Einstiegsversion.",
            bg=WHITE,
            fg=PRIMARY_GREEN,
            font=("Arial", 12, "bold"),
        ).grid(row=1, column=1, sticky="w", padx=(0, 18), pady=(4, 0))
        tk.Label(
            status_box,
            text=(
                "MM SimpleTools DokumentenSortierer Pro ist das kostenpflichtige\n"
                "Hauptprodukt mit erweiterten Dokumenten- und PDF-Funktionen."
            ),
            bg=WHITE,
            fg=PRIMARY_GREEN,
            font=("Arial", 12),
            justify="left",
        ).grid(row=2, column=1, sticky="w", padx=(0, 18), pady=(0, 8))

    def create_logo_widget(self, parent):
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")

        if Image is not None and ImageTk is not None and os.path.exists(icon_path):
            try:
                logo_image = Image.open(icon_path)
                logo_image = logo_image.resize((82, 82), Image.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_image)
                return tk.Label(parent, image=self.logo_photo, bg=WHITE, width=82, height=82)
            except Exception:
                pass

        logo = tk.Canvas(parent, width=82, height=82, bg=WHITE, bd=0, highlightthickness=0)
        draw_rounded_rectangle(logo, 0, 0, 82, 82, 10, fill=NAVY, outline=NAVY)
        logo.create_text(41, 29, text="MM", fill=WHITE, font=("Arial", 20, "bold"))
        logo.create_text(41, 51, text="SIMPLE", fill=WHITE, font=("Arial", 8, "bold"))
        logo.create_text(41, 64, text="TOOLS", fill=WHITE, font=("Arial", 8, "bold"))
        return logo

    def build_main_body(self):
        body_container = tk.Frame(self.root, bg=PAGE_BG)
        body_container.pack(fill="both", expand=True)
        body_container.columnconfigure(0, weight=0, minsize=560)
        body_container.columnconfigure(1, weight=1)
        body_container.rowconfigure(0, weight=1)

        left_host, left_content = self.create_scrollable_pane(body_container, width=560, bg=WHITE)
        left_host.grid(row=0, column=0, sticky="nsew")
        self.left_canvas = left_host.canvas

        right_host, right_content = self.create_scrollable_pane(body_container, bg=PAGE_BG)
        right_host.grid(row=0, column=1, sticky="nsew")
        self.right_canvas = right_host.canvas

        self.build_left_pane(left_content)
        self.build_right_pane(right_content)

    def create_scrollable_pane(self, parent, width=None, bg=PAGE_BG):
        host = tk.Frame(parent, bg=bg)
        if width is not None:
            host.configure(width=width)
            host.grid_propagate(False)
        host.columnconfigure(0, weight=1)
        host.rowconfigure(0, weight=1)

        canvas = tk.Canvas(host, bg=bg, bd=0, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")

        vertical_scrollbar = tk.Scrollbar(host, orient="vertical", command=canvas.yview)
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")

        horizontal_scrollbar = tk.Scrollbar(host, orient="horizontal", command=canvas.xview)
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")

        canvas.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set,
        )

        content = tk.Frame(canvas, bg=bg)
        window = canvas.create_window((0, 0), window=content, anchor="nw")

        def update_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            if width is None:
                canvas.itemconfigure(window, width=max(canvas.winfo_width(), content.winfo_reqwidth()))
            else:
                canvas.itemconfigure(window, width=max(width, content.winfo_reqwidth()))

        def scroll_vertical(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        content.bind("<Configure>", update_scroll_region)
        canvas.bind("<Configure>", update_scroll_region)
        canvas.bind("<MouseWheel>", scroll_vertical)
        host.canvas = canvas

        return host, content

    def build_left_pane(self, parent):
        left = tk.Frame(parent, bg=WHITE, width=560, highlightbackground=BORDER, highlightthickness=1)
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
            "✎  Dateien umbenennen",
            self.rename_files,
            bg=PRIMARY_GREEN,
            fg=WHITE,
            border=PRIMARY_GREEN,
            bold=True,
        ).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(14, 8))

        self.create_button(
            rename_card,
            "↩  Letzte Umbenennung rückgängig",
            self.undo_last_rename,
            bg=WHITE,
            fg=TEXT,
            border=BORDER,
        ).grid(row=6, column=0, columnspan=2, sticky="ew")

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
        right = tk.Frame(parent, bg=PAGE_BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        tk.Label(
            right,
            text=f"SICHTBARE, GESPERRTE UPGRADE-FUNKTIONEN – {UPGRADE_PRODUCT.upper()}",
            bg=PAGE_BG,
            fg=AMBER,
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(18, 10))

        banner = tk.Frame(right, bg=LIGHT_AMBER, highlightbackground=AMBER, highlightthickness=1)
        banner.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        banner.columnconfigure(1, weight=1)
        lock_canvas = tk.Canvas(banner, width=50, height=40, bg=LIGHT_AMBER, bd=0, highlightthickness=0)
        lock_canvas.grid(row=0, column=0, sticky="n", padx=(14, 10), pady=10)
        lock_canvas.create_arc(9, 5, 29, 25, start=0, extent=180, outline=AMBER, width=3, style="arc")
        lock_canvas.create_rectangle(7, 18, 31, 36, fill=AMBER, outline=AMBER)
        lock_canvas.create_oval(28, 22, 44, 38, fill="#374151", outline="#374151")
        lock_canvas.create_text(36, 30, text="+", fill=WHITE, font=("Arial", 9, "bold"))
        tk.Label(
            banner,
            text=(
                f"{UPGRADE_PRODUCT} ist das kostenpflichtige Upgrade für automatische "
                "Dokumenten-Sortierung, erweiterte PDF-Funktionen und Dateiaktionen."
            ),
            bg=LIGHT_AMBER,
            fg="#8a4b00",
            font=("Arial", 12, "bold"),
            wraplength=880,
            justify="left",
        ).grid(row=0, column=1, sticky="ew", padx=(0, 18), pady=12)

        grid = tk.Frame(right, bg=PAGE_BG)
        grid.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 6))
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
                padx=5,
                pady=4,
            )

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
        card_bg = WHITE
        card = tk.Frame(parent, bg=card_bg, highlightbackground=BORDER, highlightthickness=1, padx=10, pady=7)
        card.columnconfigure(1, weight=1)

        icon_canvas = tk.Canvas(card, width=56, height=50, bg=card_bg, bd=0, highlightthickness=0)
        icon_canvas.grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 10), pady=0)
        self.draw_locked_icon(icon_canvas, icon)

        wrap_length = 780 if is_wide else 350
        tk.Label(
            card,
            text=title,
            bg=card_bg,
            fg=TEXT,
            font=("Arial", 10, "bold" if is_wide else "normal"),
            wraplength=wrap_length,
            justify="left",
        ).grid(row=0, column=1, sticky="w")

        tk.Label(
            card,
            text=f"Verfügbar in {UPGRADE_PRODUCT}",
            bg=card_bg,
            fg="#a95700",
            font=("Arial", 8),
            wraplength=wrap_length,
            justify="left",
        ).grid(row=1, column=1, sticky="w", pady=(3, 0))

        return card

    def draw_locked_icon(self, canvas, icon_kind):
        canvas.create_rectangle(4, 3, 45, 48, fill="#f0f1f3", outline="#f0f1f3")
        color = "#90979f"

        if icon_kind in {"doc", "bill", "pdf", "undo"}:
            canvas.create_rectangle(17, 8, 36, 39, fill="#f8f9fa", outline=color, width=2)
            canvas.create_polygon(36, 8, 44, 16, 36, 16, fill="#e4e7eb", outline=color)
            canvas.create_line(21, 22, 34, 22, fill=color, width=2)
            canvas.create_line(21, 27, 34, 27, fill=color, width=2)
            if icon_kind == "undo":
                canvas.create_text(27, 27, text="↩", fill=color, font=("Arial", 14, "bold"))
        elif icon_kind == "folder":
            canvas.create_polygon(11, 19, 23, 19, 26, 24, 43, 24, 43, 40, 11, 40, fill="#d7dbe0", outline=color)
        elif icon_kind == "mail":
            canvas.create_rectangle(12, 15, 43, 38, fill="#d7dbe0", outline=color)
            canvas.create_line(12, 15, 28, 29, 43, 15, fill=color, width=2)
        elif icon_kind == "date":
            canvas.create_rectangle(13, 12, 42, 40, fill="#f8f9fa", outline=color, width=2)
            canvas.create_line(13, 20, 42, 20, fill=color, width=2)
            for x in (20, 29, 37):
                canvas.create_oval(x - 2, 27, x + 2, 31, fill=color, outline=color)
        elif icon_kind == "bank":
            canvas.create_polygon(11, 20, 28, 10, 45, 20, fill=color, outline=color)
            canvas.create_rectangle(14, 35, 42, 39, fill=color, outline=color)
            for x in (18, 28, 38):
                canvas.create_rectangle(x - 2, 22, x + 2, 35, fill=color, outline=color)
        elif icon_kind == "name":
            canvas.create_text(19, 23, text="A", fill=color, font=("Arial", 15, "bold"))
            canvas.create_text(34, 23, text="I", fill=color, font=("Arial", 15, "italic"))
            canvas.create_text(22, 36, text="7", fill=color, font=("Arial", 11, "italic"))
        elif icon_kind == "legal":
            canvas.create_line(28, 12, 28, 37, fill=color, width=3)
            canvas.create_line(17, 18, 41, 18, fill=color, width=2)
            canvas.create_text(17, 31, text="⚖", fill=color, font=("Arial", 17))
        elif icon_kind == "contract":
            canvas.create_text(27, 26, text="🤝", fill=color, font=("Arial", 17))

        canvas.create_rectangle(38, 34, 52, 50, fill="#4b5563", outline="#4b5563")
        canvas.create_arc(40, 27, 50, 43, start=0, extent=180, outline="#4b5563", width=2, style="arc")
        canvas.create_text(45, 42, text="●", fill=WHITE, font=("Arial", 5))

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
        self.left_canvas.xview_moveto(0)
        self.left_canvas.yview_moveto(0)
        self.right_canvas.xview_moveto(0)
        self.right_canvas.yview_moveto(0)
        self.center_window()

    def show_all_content(self):
        self.root.state("zoomed")
        self.left_canvas.xview_moveto(0)
        self.left_canvas.yview_moveto(0)
        self.right_canvas.xview_moveto(0)
        self.right_canvas.yview_moveto(0)

    def select_folder(self):
        selected_folder = filedialog.askdirectory()

        if selected_folder:
            self.folder_path.set(selected_folder)

    def rename_files(self):
        folder = self.folder_path.get()
        prefix = self.prefix.get().strip()
        start_number_text = self.start_number.get().strip()

        if not folder:
            messagebox.showerror("Fehler", "Bitte zuerst einen Ordner auswählen.")
            return

        if not prefix:
            messagebox.showerror("Fehler", "Bitte einen Dateinamen / Prefix eingeben.")
            return

        if not start_number_text.isdigit():
            messagebox.showerror("Fehler", "Die Startnummer muss eine Zahl sein.")
            return

        start_number = int(start_number_text)

        try:
            files = [
                file for file in os.listdir(folder)
                if os.path.isfile(os.path.join(folder, file))
            ]

            if not files:
                messagebox.showinfo("Hinweis", "Im ausgewählten Ordner wurden keine Dateien gefunden.")
                return

            files.sort()

            renamed_count = 0
            rename_operations = []
            number = start_number

            for file in files:
                old_path = os.path.join(folder, file)

                file_extension = os.path.splitext(file)[1]
                new_filename = f"{prefix}{number:03d}{file_extension}"
                new_path = os.path.join(folder, new_filename)

                while os.path.exists(new_path):
                    number += 1
                    new_filename = f"{prefix}{number:03d}{file_extension}"
                    new_path = os.path.join(folder, new_filename)

                os.rename(old_path, new_path)
                rename_operations.append(
                    {
                        "old_path": old_path,
                        "new_path": new_path,
                    }
                )

                renamed_count += 1
                number += 1

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
