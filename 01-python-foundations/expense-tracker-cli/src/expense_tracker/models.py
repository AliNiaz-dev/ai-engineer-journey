"""Data models and validation helpers for expenses."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any

from expense_tracker.exceptions import ValidationError

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")


def validate_date(date_str: str) -> str:
    """Validate that a date string strictly follows YYYY-MM-DD format."""
    if not isinstance(date_str, str):
        raise ValidationError("Date must be a string in YYYY-MM-DD format.")

    cleaned = date_str.strip()
    if not DATE_PATTERN.match(cleaned):
        raise ValidationError("Date must follow YYYY-MM-DD format (e.g., 2026-11-26).")

    try:
        datetime.strptime(cleaned, "%Y-%m-%d")
    except ValueError as exc:
        raise ValidationError(f"Invalid calendar date: '{cleaned}'.") from exc

    return cleaned


def validate_month(month_str: str) -> str:
    """Validate that a month string strictly follows YYYY-MM format."""
    if not isinstance(month_str, str):
        raise ValidationError("Month must be a string in YYYY-MM format.")

    cleaned = month_str.strip()
    if not MONTH_PATTERN.match(cleaned):
        raise ValidationError("Month must follow YYYY-MM format (e.g., 2026-11).")

    try:
        datetime.strptime(cleaned, "%Y-%m")
    except ValueError as exc:
        raise ValidationError(f"Invalid month: '{cleaned}'.") from exc

    return cleaned


@dataclass
class Expense:
    """Represents a single recorded expense."""

    id: int
    title: str
    amount: float
    category: str
    date: str
    note: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.id, int) or isinstance(self.id, bool) or self.id <= 0:
            raise ValidationError("Expense ID must be a positive integer.")

        if not isinstance(self.title, str) or not self.title.strip():
            raise ValidationError("Expense title cannot be empty.")
        self.title = self.title.strip()

        if not isinstance(self.category, str) or not self.category.strip():
            raise ValidationError("Expense category cannot be empty.")
        self.category = self.category.strip()

        if isinstance(self.amount, bool):
            raise ValidationError("Expense amount must be a number greater than zero.")
        try:
            numeric_amount = float(self.amount)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Expense amount must be a valid number.") from exc

        if numeric_amount <= 0:
            raise ValidationError("Expense amount must be greater than zero.")
        self.amount = round(numeric_amount, 2)

        self.date = validate_date(self.date)
        self.note = self.note.strip() if isinstance(self.note, str) else ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the expense into a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "amount": self.amount,
            "category": self.category,
            "date": self.date,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Expense:
        """Create an Expense instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValidationError("Expense record must be a dictionary.")

        required_keys = ("id", "title", "amount", "category", "date")
        missing = [key for key in required_keys if key not in data]
        if missing:
            raise ValidationError(f"Missing required expense fields: {', '.join(missing)}")

        return cls(
            id=data["id"],
            title=data["title"],
            amount=data["amount"],
            category=data["category"],
            date=data["date"],
            note=data.get("note", ""),
        )
