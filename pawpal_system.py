from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Pet:
    name: str
    species: str
    age: int

    def get_label(self) -> str:
        """Return a human-readable label for the pet (e.g. 'Mochi the dog')."""
        pass


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str          # "low" | "medium" | "high"
    notes: Optional[str] = None

    def fits_within(self, budget_minutes: int) -> bool:
        """Return True if this task's duration fits inside the remaining budget."""
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: str = ""

    def get_available_time(self) -> int:
        """Return the owner's total available time in minutes for the day."""
        pass


@dataclass
class DailyPlan:
    scheduled_tasks: list[Task] = field(default_factory=list)
    total_duration_minutes: int = 0
    reasoning: list[str] = field(default_factory=list)

    def display(self) -> str:
        """Return a formatted string listing each scheduled task and its duration."""
        pass

    def explain(self) -> str:
        """Return the reasoning for why each task was included or skipped."""
        pass


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet, tasks: list[Task]):
        self.owner = owner
        self.pet = pet
        self.tasks = tasks

    def generate_schedule(self) -> DailyPlan:
        """Select and order tasks that fit within the owner's available time."""
        pass

    def _filter_by_priority(self) -> list[Task]:
        """Return tasks sorted from highest to lowest priority."""
        pass

    def _fits_in_time(self, tasks: list[Task], budget: int) -> list[Task]:
        """Return the subset of tasks that cumulatively fit inside budget_minutes."""
        pass
