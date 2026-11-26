"""Storage abstractions and JSON persistence for expenses."""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
from pathlib import Path
import shutil

from expense_tracker.exceptions import StorageError, ValidationError
from expense_tracker.models import Expense


class BaseStorage(ABC):
    """Abstract base class defining the storage interface for expenses."""

    @abstractmethod
    def load(self) -> list[Expense]:
        """Load and return all stored expenses."""

    @abstractmethod
    def save(self, expenses: list[Expense]) -> None:
        """Persist the given list of expenses."""


class JsonStorage(BaseStorage):
    """Stores expenses permanently in a UTF-8 JSON file."""

    def __init__(self, file_path: Path | str) -> None:
        self._file_path = Path(file_path)
        self.last_warning: str | None = None

    @property
    def file_path(self) -> Path:
        """Return the path to the backing JSON file."""
        return self._file_path

    def load(self) -> list[Expense]:
        """Load expenses from JSON, safely handling missing or corrupted files."""
        self.last_warning = None

        if not self._file_path.exists():
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            return []

        try:
            raw_text = self._file_path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise StorageError(f"Unable to read '{self._file_path}': {exc}") from exc

        if not raw_text:
            return []

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            self._backup_corrupted_file()
            self.last_warning = (
                f"Corrupted JSON detected in '{self._file_path.name}'. "
                "A backup was created and an empty list was loaded."
            )
            return []

        if not isinstance(data, list):
            self._backup_corrupted_file()
            self.last_warning = (
                f"Unexpected JSON format in '{self._file_path.name}'. "
                "Expected a list; starting with an empty list."
            )
            return []

        expenses: list[Expense] = []
        skipped = 0
        for item in data:
            try:
                expenses.append(Expense.from_dict(item))
            except ValidationError:
                skipped += 1

        if skipped > 0:
            self.last_warning = f"Skipped {skipped} invalid expense record(s) while loading."

        return expenses

    def save(self, expenses: list[Expense]) -> None:
        """Write all expenses to the JSON file safely."""
        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            payload = [expense.to_dict() for expense in expenses]
            temp_path = self._file_path.with_suffix(".tmp")
            with temp_path.open("w", encoding="utf-8") as file_handle:
                json.dump(payload, file_handle, indent=2)
            temp_path.replace(self._file_path)
        except OSError as exc:
            raise StorageError(f"Failed to save expenses to '{self._file_path}': {exc}") from exc

    def _backup_corrupted_file(self) -> None:
        """Preserve a corrupted JSON file as a .bak copy before continuing."""
        backup_path = self._file_path.with_suffix(self._file_path.suffix + ".bak")
        try:
            shutil.copy2(self._file_path, backup_path)
        except OSError:
            pass


class InMemoryStorage(BaseStorage):
    """In-memory storage implementation useful for testing."""

    def __init__(self, initial_expenses: list[Expense] | None = None) -> None:
        self._expenses: list[Expense] = list(initial_expenses) if initial_expenses else []

    def load(self) -> list[Expense]:
        """Return a copy of the in-memory expenses."""
        return list(self._expenses)

    def save(self, expenses: list[Expense]) -> None:
        """Replace in-memory expenses with a copy of the provided list."""
        self._expenses = list(expenses)
