"""PDF tools for MM SimpleTools FileRenamer V2.0."""

import os

from pypdf import PdfReader, PdfWriter


class InvalidPdfError(ValueError):
    """Raised when a selected file is not a readable PDF."""

    def __init__(self, filename: str, details: str | None = None):
        self.filename = filename
        self.details = details

        if details:
            message = f"Fehler beim Lesen von Datei {filename}: {details}"
        else:
            message = f"Keine gültige PDF-Datei: {filename}"

        super().__init__(message)


class NotEnoughPdfFilesError(ValueError):
    """Raised when fewer than two PDF files were selected for merging."""

    def __init__(self):
        super().__init__("Bitte mindestens zwei PDF-Dateien auswählen.")


def _display_name(file_path: str) -> str:
    return os.path.basename(file_path) or file_path


def _ensure_valid_pdf_file(file_path: str) -> str:
    normalized_path = os.path.abspath(file_path)
    filename = _display_name(file_path)

    if not os.path.exists(normalized_path):
        raise FileNotFoundError(f"PDF-Datei nicht gefunden: {filename}")

    if not os.path.isfile(normalized_path):
        raise ValueError(f"Keine Datei: {filename}")

    if not normalized_path.lower().endswith(".pdf"):
        raise InvalidPdfError(filename)

    try:
        with open(normalized_path, "rb") as input_stream:
            file_header = input_stream.read(4)
    except OSError as error:
        raise OSError(f"Fehler beim Lesen von Datei {filename}: {error}") from error

    if file_header != b"%PDF":
        raise InvalidPdfError(filename)

    return normalized_path


def validate_pdf_file(file_path: str) -> str:
    """Validate one selected PDF file and return its absolute path."""
    return _ensure_valid_pdf_file(file_path)


def merge_pdfs(input_files: list[str], output_file: str) -> None:
    """Merge multiple PDF files into one output PDF.

    The input files are read in the order provided. Original files are never
    modified.
    """
    if len(input_files) < 2:
        raise NotEnoughPdfFilesError()

    if not output_file:
        raise ValueError("Bitte eine Ziel-PDF-Datei auswählen.")

    if not output_file.lower().endswith(".pdf"):
        raise ValueError("Die Ausgabedatei muss auf .pdf enden.")

    normalized_output = os.path.abspath(output_file)
    writer = PdfWriter()

    for input_file in input_files:
        if not input_file:
            raise ValueError("Die Dateiauswahl enthält einen leeren Eintrag.")

        normalized_input = _ensure_valid_pdf_file(input_file)

        if normalized_input == normalized_output:
            raise ValueError("Die Ziel-PDF darf keine der Originaldateien überschreiben.")

        filename = _display_name(normalized_input)

        try:
            reader = PdfReader(normalized_input, strict=True)

            for page in reader.pages:
                writer.add_page(page)

        except Exception as error:
            raise InvalidPdfError(filename, str(error)) from error

    try:
        with open(normalized_output, "wb") as output_stream:
            writer.write(output_stream)

    except Exception as error:
        raise RuntimeError(f"Ziel-PDF konnte nicht geschrieben werden: {error}") from error
