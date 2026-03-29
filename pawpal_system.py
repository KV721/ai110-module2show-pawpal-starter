from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Task:
    title: str
    description: str
    duration_minutes: int
    priority: Priority
    frequency: str = "daily"   # "daily" | "weekly" | "as-needed"
    completed: bool = False

    def fits_within(self, budget_minutes: int) -> bool:
        """Return True if this task's duration fits inside the remaining budget."""
        return self.duration_minutes <= budget_minutes

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def reset(self) -> None:
        """Reset completion status (e.g. at the start of a new day)."""
        self.completed = False


@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def get_label(self) -> str:
        """Return a human-readable label, e.g. 'Mochi the dog'."""
        return f"{self.name} the {self.species}"

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove a task by title. No-op if not found."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks that have not yet been completed."""
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)
    preferences: str = ""

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's roster."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove a pet by name. No-op if not found."""
        self.pets = [p for p in self.pets if p.name != name]

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all pets this owner manages."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_available_time(self) -> int:
        """Return the owner's total available time in minutes for the day."""
        return self.available_minutes


@dataclass
class DailyPlan:
    scheduled_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    total_duration_minutes: int = 0
    reasoning: list[str] = field(default_factory=list)
    skipped_reasons: list[str] = field(default_factory=list)

    def display(self) -> str:
        """Return a formatted string listing each scheduled task and its duration."""
        if not self.scheduled_tasks:
            return "No tasks scheduled for today."
        lines = ["--- Daily Plan ---"]
        for task in self.scheduled_tasks:
            lines.append(
                f"[{task.priority.name}] {task.title} — {task.duration_minutes} min"
            )
        lines.append(f"\nTotal time: {self.total_duration_minutes} min")
        return "\n".join(lines)

    def explain(self) -> str:
        """Return the reasoning for why each task was included or skipped."""
        lines = ["--- Schedule Explanation ---"]
        for r in self.reasoning:
            lines.append(f"  included: {r}")
        for r in self.skipped_reasons:
            lines.append(f"  skipped:  {r}")
        return "\n".join(lines)


class Scheduler:
    """The scheduling brain. Retrieves, organizes, and manages tasks across all pets."""

    def __init__(self, owner: Owner):
        self.owner = owner

    def generate_schedule(self) -> DailyPlan:
        """Build a daily plan from all pending tasks across every pet.

        Steps:
          1. Collect all incomplete tasks from every pet the owner manages.
          2. Sort by priority (highest first).
          3. Greedily fill the owner's time budget.
          4. Record reasoning for included and skipped tasks.
        """
        plan = DailyPlan()
        budget = self.owner.get_available_time()

        pending = [t for t in self.owner.get_all_tasks() if not t.completed]
        sorted_tasks = self._filter_by_priority(pending)
        selected, skipped = self._fits_in_time(sorted_tasks, budget)

        for task in selected:
            plan.scheduled_tasks.append(task)
            plan.total_duration_minutes += task.duration_minutes
            plan.reasoning.append(
                f"'{task.title}' — {task.priority.name} priority, {task.duration_minutes} min"
            )

        for task in skipped:
            plan.skipped_tasks.append(task)
            plan.skipped_reasons.append(
                f"'{task.title}' — needs {task.duration_minutes} min, not enough time remaining"
            )

        return plan

    def _filter_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted from highest to lowest priority."""
        return sorted(tasks, key=lambda t: t.priority.value, reverse=True)

    def _fits_in_time(
        self, tasks: list[Task], budget: int
    ) -> tuple[list[Task], list[Task]]:
        """Greedily select tasks that fit within the budget.

        Returns a tuple of (selected, skipped).
        """
        selected: list[Task] = []
        skipped: list[Task] = []
        remaining = budget
        for task in tasks:
            if task.fits_within(remaining):
                selected.append(task)
                remaining -= task.duration_minutes
            else:
                skipped.append(task)
        return selected, skipped

    def mark_task_complete(self, title: str) -> None:
        """Mark the first task matching the given title as complete, across all pets."""
        for task in self.owner.get_all_tasks():
            if task.title == title:
                task.mark_complete()
                return

    def reset_all_tasks(self) -> None:
        """Reset every task to incomplete (call at the start of a new day)."""
        for task in self.owner.get_all_tasks():
            task.reset()

    def get_tasks_for_pet(self, pet_name: str) -> list[Task]:
        """Return all tasks belonging to a specific pet by name."""
        for pet in self.owner.pets:
            if pet.name == pet_name:
                return pet.tasks
        return []
