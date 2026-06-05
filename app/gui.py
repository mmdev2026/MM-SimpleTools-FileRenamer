"""Tkinter user interface for MM SimpleTools FileRenamer."""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

from app.pdf_tools import InvalidPdfError, NotEnoughPdfFilesError, merge_pdfs, validate_pdf_file
from app.undo_manager import UndoManager


APP_NAME = "MM SimpleTools - FileRenamer"
APP_VERSION = "2.0"


class FileRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} V{APP_VERSION}")
        self.window_width = 760
        self.window_height = 620
        self.root.minsize(640, 520)
        self.root.resizable(True, True)

        self.folder_path = tk.StringVar()
        self.prefix = tk.StringVar(value="IMG_")
        self.start_number = tk.StringVar(value="1")
        self.undo_manager = UndoManager()

        self.build_ui()
        self.center_window()

    def center_window(self):
        self.root.update_idletasks()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_position = max((screen_width - self.window_width) // 2, 0)
        y_position = max((screen_height - self.window_height) // 2, 0)

        self.root.geometry(f"{self.window_width}x{self.window_height}+{x_position}+{y_position}")

    def build_ui(self):
        title_label = tk.Label(
            self.root,
            text=f"{APP_NAME} V{APP_VERSION}",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=12)

        rename_frame = tk.LabelFrame(self.root, text="Dateien umbenennen", padx=10, pady=8)
        rename_frame.pack(pady=8, padx=15, fill="x")

        folder_frame = tk.Frame(rename_frame)
        folder_frame.pack(pady=8, padx=15, fill="x")

        tk.Label(folder_frame, text="Ordner:").pack(anchor="w")

        folder_entry = tk.Entry(
            folder_frame,
            textvariable=self.folder_path,
            width=55,
            state="readonly"
        )
        folder_entry.pack(side="left", padx=(0, 8), fill="x", expand=True)

        browse_button = tk.Button(
            folder_frame,
            text="Auswählen",
            command=self.select_folder
        )
        browse_button.pack(side="right")

        prefix_frame = tk.Frame(rename_frame)
        prefix_frame.pack(pady=8, padx=15, fill="x")

        tk.Label(prefix_frame, text="Dateiname / Prefix:").pack(anchor="w")

        prefix_entry = tk.Entry(
            prefix_frame,
            textvariable=self.prefix,
            width=30
        )
        prefix_entry.pack(anchor="w")

        number_frame = tk.Frame(rename_frame)
        number_frame.pack(pady=8, padx=15, fill="x")

        tk.Label(number_frame, text="Startnummer:").pack(anchor="w")

        number_entry = tk.Entry(
            number_frame,
            textvariable=self.start_number,
            width=10
        )
        number_entry.pack(anchor="w")

        rename_button = tk.Button(
            rename_frame,
            text="Dateien umbenennen",
            font=("Arial", 12, "bold"),
            width=25,
            height=2,
            command=self.rename_files
        )
        rename_button.pack(pady=(14, 6))

        undo_button = tk.Button(
            rename_frame,
            text="Rückgängig",
            width=25,
            command=self.undo_last_rename
        )
        undo_button.pack(pady=(0, 8))

        pdf_frame = tk.LabelFrame(self.root, text="PDF-Tools", padx=10, pady=10)
        pdf_frame.pack(pady=8, padx=15, fill="x")

        pdf_buttons_frame = tk.Frame(pdf_frame)
        pdf_buttons_frame.pack(fill="x")

        merge_pdf_button = tk.Button(
            pdf_buttons_frame,
            text="PDFs zusammenführen",
            width=25,
            command=self.merge_selected_pdfs
        )
        merge_pdf_button.grid(row=0, column=0, sticky="w", padx=(0, 16))

        extract_pdf_frame = tk.Frame(pdf_buttons_frame)
        extract_pdf_frame.grid(row=0, column=1, sticky="w")

        extract_pdf_button = tk.Button(
            extract_pdf_frame,
            text="PDF-Seiten extrahieren",
            width=25,
            state="disabled"
        )
        extract_pdf_button.pack(anchor="w")

        extract_hint_label = tk.Label(
            extract_pdf_frame,
            text="PDF-Seiten extrahieren: vorbereitet für spätere Version",
            font=("Arial", 8),
            fg="gray"
        )
        extract_hint_label.pack(anchor="w", pady=(4, 0))

        info_label = tk.Label(
            self.root,
            text="Lokal ausgeführt. Keine Datenübertragung.",
            font=("Arial", 9)
        )
        info_label.pack(pady=4)

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
            "Diese PDF-Funktion ist für V2.0 vorbereitet und wird im nächsten Schritt implementiert."
        )
