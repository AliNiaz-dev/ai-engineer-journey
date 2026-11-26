"""Core business logic for managing expenses."""

from __future__ import annotations

from datetime import date as dt_date
from typing import Callable, Iterator

from expense_tracker.exceptions import (
    DuplicateExpenseError,
    ExpenseNotFoundError,
    ValidationError,
)
from expense_tracker.models import Expense, validate_month
from expense_tracker.storage import BaseStorage


class ExpenseManager:
    """Manages adding, viewing, deleting, searching, and filtering expenses."""

    def __init__(self, storage: BaseStorage) -> None:
        self._storage = storage
        self._expenses: list[Expense] = self._storage.load()

    def __len__(self) -> int:
        return len(self._expenses)

    def __iter__(self) -> Iterator[Expense]:
        return iter(self._expenses)

    @property
    def expenses(self) -> list[Expense]:
        """Return a shallow copy of all stored expenses."""
        return list(self._expenses)

    def _next_id(self) -> int:
        """Generate the next unique positive integer ID."""
        return max((expense.id for expense in self._expenses), default=0) + 1

    def add_expense(
        self,
        title: str,
        amount: float,
        category: str,
        expense_date: str | None = None,
        note: str = "",
        expense_id: int | None = None,
    ) -> Expense:
        """Validate, create, and persist a new expense."""
        resolved_id = self._next_id() if expense_id is None else expense_id

        if any(existing.id == resolved_id for existing in self._expenses):
            raise DuplicateExpenseError(f"Expense with ID {resolved_id} already exists.")

        resolved_date = (
            dt_date.today().isoformat()
            if expense_date is None or not str(expense_date).strip()
            else expense_date
        )

        expense = Expense(
            id=resolved_id,
            title=title,
            amount=amount,
            category=category,
            date=resolved_date,
            note=note,
        )
        self._expenses.append(expense)
        self._storage.save(self._expenses)
        return expense

    def delete_expense(self, expense_id: int) -> Expense:
        """Delete an expense by its ID and persist the updated list."""
        for index, expense in enumerate(self._expenses):
            if expense.id == expense_id:
                removed = self._expenses.pop(index)
                self._storage.save(self._expenses)
                return removed

        raise ExpenseNotFoundError(f"No expense found with ID {expense_id}.")

    def get_all_expenses(self, sort_by: str = "date", reverse: bool = True) -> list[Expense]:
        """Return all expenses sorted by the specified field."""
        sort_keys: dict[str, Callable[[Expense], object]] = {
            "id": lambda e: e.id,
            "amount": lambda e: e.amount,
            "date": lambda e: (e.date, e.id),
            "category": lambda e: e.category.lower(),
            "title": lambda e: e.title.lower(),
        }
        key_fn = sort_keys.get(sort_by)
        if key_fn is None:
            raise ValidationError(
                f"Invalid sort field '{sort_by}'. Choose from: {', '.join(sort_keys)}."
            )
        return sorted(self._expenses, key=key_fn, reverse=reverse)

    def iter_expenses(self) -> Iterator[Expense]:
        """Yield expenses lazily one by one."""
        for expense in self._expenses:
            yield expense

    def search_expenses(self, query: str) -> list[Expense]:
        """Search expenses whose title or note contains the query (case-insensitive)."""
        cleaned = query.strip().lower()
        if not cleaned:
            return []

        return [
            expense
            for expense in self._expenses
            if cleaned in expense.title.lower() or cleaned in expense.note.lower()
        ]

    def filter_by_category(self, category: str) -> list[Expense]:
        """Return expenses matching the given category (case-insensitive)."""
        cleaned = category.strip().lower()
        if not cleaned:
            return []

        return [
            expense
            for expense in self._expenses
            if expense.category.lower() == cleaned
        ]

    def filter_by_month(self, month: str) -> list[Expense]:
        """Return expenses occurring in the given YYYY-MM month."""
        validated_month = validate_month(month)
        return [
            expense
            for expense in self._expenses
            if expense.date.startswith(validated_month)
        ]

    def get_categories(self) -> set[str]:
        """Return the set of unique categories across all expenses."""
        return {expense.category for expense in self._expenses}

    def total_expenses(self) -> float:
        """Return the sum of all expense amounts rounded to two decimal places."""
        return round(sum(expense.amount for expense in self._expenses), 2)
