"""Undo history module for MM SimpleTools DokumentenSortierer Pro."""

from datetime import datetime
import json
import os


HISTORY_FILENAME = "rename_history.json"


class UndoManager:
    """Manages rename history persistence and undo operations."""

    def __init__(self, history_path=None):
        self.history_path = history_path or self._default_history_path()

    def _default_history_path(self):
        app_data = os.environ.get("APPDATA")

        if app_data:
            return os.path.join(app_data, "MM SimpleTools", "DokumentenSortierer Pro", HISTORY_FILENAME)

        return os.path.join(os.path.expanduser("~"), HISTORY_FILENAME)

    def history_exists(self):
        return os.path.exists(self.history_path)

    def load_history(self):
        if not self.history_exists():
            return []

        with open(self.history_path, "r", encoding="utf-8") as history_file:
            return json.load(history_file)

    def save_history(self, history):
        history_folder = os.path.dirname(self.history_path)

        if history_folder:
            os.makedirs(history_folder, exist_ok=True)

        with open(self.history_path, "w", encoding="utf-8") as history_file:
            json.dump(history, history_file, indent=2, ensure_ascii=False)

    def record_rename(self, folder, operations):
        history = self.load_history()
        history.append(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "folder": folder,
                "operations": operations,
            }
        )
        self.save_history(history)

    def undo_last_rename(self):
        history = self.load_history()

        if not history:
            raise ValueError("Es ist keine Umbenennung zum Rückgängig machen vorhanden.")

        last_entry = history[-1]
        operations = last_entry.get("operations", [])

        if not operations:
            raise ValueError("Der letzte Verlaufseintrag enthält keine Umbenennungen.")

        for operation in reversed(operations):
            old_path = operation["old_path"]
            new_path = operation["new_path"]

            if not os.path.exists(new_path):
                raise FileNotFoundError(f"Datei nicht gefunden: {new_path}")

            if os.path.exists(old_path):
                raise FileExistsError(f"Zieldatei existiert bereits: {old_path}")

        for operation in reversed(operations):
            os.rename(operation["new_path"], operation["old_path"])

        history.pop()
        self.save_history(history)

        return len(operations)
