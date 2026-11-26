"""Python knowledge quiz module for the Expense Tracker CLI."""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class QuizQuestion:
    """
    Represents a single multiple-choice quiz question.

    Demonstrates dataclasses with default_factory for mutable defaults.
    """

    question: str
    options: list[str]           # labelled A, B, C, D
    correct_index: int           # 0-based index into options
    explanation: str = ""

    @property
    def correct_letter(self) -> str:
        """Return the letter ('A', 'B', 'C', 'D') of the correct option."""
        return chr(ord("A") + self.correct_index)

    @property
    def correct_answer(self) -> str:
        """Return the full text of the correct option."""
        return self.options[self.correct_index]


# ── Question bank ─────────────────────────────────────────────────────────────
QUESTION_BANK: list[QuizQuestion] = [
    QuizQuestion(
        question="What keyword is used to define a function in Python?",
        options=["func", "define", "def", "function"],
        correct_index=2,
        explanation="The 'def' keyword introduces a function definition.",
    ),
    QuizQuestion(
        question="Which of the following is an IMMUTABLE Python data type?",
        options=["list", "dict", "set", "tuple"],
        correct_index=3,
        explanation="Tuples cannot be changed after creation; they are immutable.",
    ),
    QuizQuestion(
        question="What does the 'self' parameter in a class method refer to?",
        options=[
            "The class itself",
            "The current instance of the class",
            "The parent class",
            "A static variable",
        ],
        correct_index=1,
        explanation="'self' refers to the specific object instance calling the method.",
    ),
    QuizQuestion(
        question="Which built-in function returns the number of items in a list?",
        options=["size()", "count()", "len()", "total()"],
        correct_index=2,
        explanation="len() returns the number of elements in any sequence or collection.",
    ),
    QuizQuestion(
        question="What is the output of:  [x**2 for x in range(3)]",
        options=["[1, 4, 9]", "[0, 1, 4]", "[0, 1, 2]", "[0, 2, 4]"],
        correct_index=1,
        explanation="range(3) gives 0, 1, 2 → squared: 0, 1, 4.",
    ),
    QuizQuestion(
        question="Which decorator is used to define a static method inside a class?",
        options=["@classmethod", "@property", "@static", "@staticmethod"],
        correct_index=3,
        explanation="@staticmethod marks a method that doesn't receive 'self' or 'cls'.",
    ),
    QuizQuestion(
        question="What module is used to read and write CSV files in Python's standard library?",
        options=["pandas", "csv", "excel", "io"],
        correct_index=1,
        explanation="The built-in 'csv' module provides reader and writer utilities.",
    ),
    QuizQuestion(
        question="What type hint represents a function that returns nothing?",
        options=["None", "Null", "void", "NoneType"],
        correct_index=0,
        explanation="'-> None' tells type checkers the function has no return value.",
    ),
    QuizQuestion(
        question="In Python, which keyword is used to handle exceptions?",
        options=["catch", "rescue", "except", "handle"],
        correct_index=2,
        explanation="Python uses try/except blocks to handle exceptions.",
    ),
    QuizQuestion(
        question="What does OOP stand for?",
        options=[
            "Object-Oriented Programming",
            "Output-Oriented Processing",
            "Open Object Protocol",
            "Ordered Object Parsing",
        ],
        correct_index=0,
        explanation="OOP is a paradigm organising code around objects and classes.",
    ),
    QuizQuestion(
        question="Which keyword creates a generator function?",
        options=["return", "yield", "async", "generate"],
        correct_index=1,
        explanation="A function containing 'yield' becomes a generator.",
    ),
    QuizQuestion(
        question="What does the 'json' module's json.loads() function do?",
        options=[
            "Writes Python data to a JSON file",
            "Parses a JSON-formatted string into a Python object",
            "Loads a JSON file from disk",
            "Converts a dict to a JSON string",
        ],
        correct_index=1,
        explanation="json.loads() deserialises a JSON *string* into Python objects.",
    ),
]


@dataclass
class QuizResult:
    """Stores the result of a completed quiz session."""

    total: int
    correct: int
    wrong_questions: list[tuple[QuizQuestion, str]] = field(default_factory=list)

    @property
    def score_percent(self) -> float:
        """Return the score as a percentage."""
        return round((self.correct / self.total * 100) if self.total else 0.0, 1)

    @property
    def grade(self) -> str:
        """Return a letter grade based on the score percentage."""
        pct = self.score_percent
        if pct >= 90:
            return "A"
        if pct >= 70:
            return "B"
        if pct >= 50:
            return "C"
        return "D"


class Quiz:
    """
    Manages a multiple-choice Python knowledge quiz.

    Demonstrates:
    - Encapsulation of quiz state
    - Dataclasses (QuizQuestion, QuizResult)
    - Randomised question selection
    - Type hints and properties
    """

    def __init__(self, num_questions: int = 10) -> None:
        self._num_questions = min(num_questions, len(QUESTION_BANK))
        self._questions: list[QuizQuestion] = random.sample(
            QUESTION_BANK, self._num_questions
        )

    def run(self) -> QuizResult:
        """Run the quiz interactively and return the result."""
        print("\n" + "=" * 60)
        print("        PYTHON KNOWLEDGE QUIZ")
        print("=" * 60)
        print(f"  Answer {self._num_questions} multiple-choice questions.")
        print("  Enter the letter of your answer (A / B / C / D).\n")

        correct_count = 0
        wrong: list[tuple[QuizQuestion, str]] = []

        for idx, q in enumerate(self._questions, start=1):
            print(f"  Q{idx}. {q.question}")
            for letter, option in zip("ABCD", q.options):
                print(f"       {letter}) {option}")

            user_answer = self._get_valid_answer()
            user_index = ord(user_answer) - ord("A")

            if user_index == q.correct_index:
                print("  ✓  Correct!\n")
                correct_count += 1
            else:
                print(
                    f"  ✗  Incorrect. Correct answer: {q.correct_letter}) {q.correct_answer}\n"
                )
                wrong.append((q, user_answer))

        result = QuizResult(
            total=self._num_questions,
            correct=correct_count,
            wrong_questions=wrong,
        )
        self._print_result(result)
        return result

    @staticmethod
    def _get_valid_answer() -> str:
        """Prompt until the user enters a valid A/B/C/D answer."""
        valid = {"A", "B", "C", "D"}
        while True:
            raw = input("  Your answer: ").strip().upper()
            if raw in valid:
                return raw
            print("  Please enter A, B, C or D.")

    @staticmethod
    def _print_result(result: QuizResult) -> None:
        """Display the final quiz score and review section."""
        print("=" * 60)
        print("        QUIZ COMPLETE")
        print("=" * 60)
        print(f"  Score : {result.correct} / {result.total}  ({result.score_percent}%)")
        print(f"  Grade : {result.grade}")

        if result.wrong_questions:
            print("\n  ─── Review — Questions You Missed ───────────────────")
            for q, answered in result.wrong_questions:
                print(f"\n  Q: {q.question}")
                print(f"     You answered   : {answered}) {q.options[ord(answered) - ord('A')]}")
                print(f"     Correct answer : {q.correct_letter}) {q.correct_answer}")
                if q.explanation:
                    print(f"     Explanation    : {q.explanation}")
        else:
            print("\n  🎉 Perfect score! Excellent work!")

        print("=" * 60)
