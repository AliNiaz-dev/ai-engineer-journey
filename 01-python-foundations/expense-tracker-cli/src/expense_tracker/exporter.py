"""CSV export functionality for the Expense Tracker."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from expense_tracker.exceptions import StorageError
from expense_tracker.models import Expense

# Column order and human-readable headers for the CSV export
CSV_FIELDNAMES: tuple[str, ...] = ("id", "title", "amount", "category", "date", "note")
CSV_HEADERS: tuple[str, ...] = ("ID", "Title", "Amount ($)", "Category", "Date", "Note")


class CSVExporter:
    """
    Exports expense data to a CSV file inside the exports directory.

    Demonstrates:
    - Encapsulation of file path construction and CSV writing
    - Type hints and dataclasses interacting with the csv module
    - Exception handling with a custom StorageError
    """

    def __init__(self, exports_dir: Path | str = "exports") -> None:
        self._exports_dir = Path(exports_dir)

    def export(self, expenses: list[Expense]) -> Path:
        """
        Write all expenses to a timestamped CSV file.

        Returns the Path of the created file.
        """
        if not expenses:
            raise StorageError("No expenses to export — the list is empty.")

        self._exports_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = self._exports_dir / f"expenses_{timestamp}.csv"

        try:
            with file_path.open("w", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDNAMES)

                # Write a custom human-readable header row
                writer.writerow(dict(zip(CSV_FIELDNAMES, CSV_HEADERS)))

                # Write each expense using its dict representation
                for expense in sorted(expenses, key=lambda e: (e.date, e.id)):
                    writer.writerow(expense.to_dict())

        except OSError as exc:
            raise StorageError(
                f"Failed to write CSV file '{file_path}': {exc}"
            ) from exc

        return file_path
