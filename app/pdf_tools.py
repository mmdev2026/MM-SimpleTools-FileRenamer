"""Prepared PDF tools module for FileRenamer V2.0.

The PDF feature implementation will be added in later steps. Keeping this
module separate prevents PDF dependencies and workflows from affecting the
existing rename behavior.
"""


class PdfTools:
    """Placeholder service for future PDF operations."""

    def merge_pdfs(self, input_paths, output_path):
        raise NotImplementedError("PDF merge will be implemented in a later step.")

    def split_pdf(self, input_path, output_folder):
        raise NotImplementedError("PDF split will be implemented in a later step.")

    def extract_pages(self, input_path, page_ranges, output_path):
        raise NotImplementedError("PDF page extraction will be implemented in a later step.")
