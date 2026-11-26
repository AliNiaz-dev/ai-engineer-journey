"""Custom exceptions for the Expense Tracker CLI application."""


class ExpenseTrackerError(Exception):
    """Base exception for all expense tracker errors."""


class ValidationError(ExpenseTrackerError):
    """Raised when expense data or user input fails validation."""


class DuplicateExpenseError(ExpenseTrackerError):
    """Raised when attempting to add an expense with an existing ID."""


class ExpenseNotFoundError(ExpenseTrackerError):
    """Raised when an expense with the given ID cannot be found."""


class StorageError(ExpenseTrackerError):
    """Raised when reading from or writing to storage fails."""
