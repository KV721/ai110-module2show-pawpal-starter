from __future__ import annotations
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from enum import Enum
from typing import Optional


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
    frequency: str = "daily"        # "daily" | "weekly" | "as-needed"
    completed: bool = False
    start_time: Optional[str] = None  # "HH:MM" — assigned by Scheduler
    due_date: Optional[date] = None

    def fits_within(self, budget_minutes: int) -> bool:
        """Return True if this task's duration fits inside the remaining budget."""
        return self.duration_minutes <= budget_minutes

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def reset(self) -> None:
        """Reset completion status (e.g. at the start of a new day)."""
        self.completed = False

    def spawn_next_occurrence(self) -> "Task":
        """Return a new Task for the next occurrence of a recurring task.

        Uses dataclasses.replace() to copy all fields, then adjusts due_date
        and clears completion state and start_time.
        Daily  → due_date + 1 day
        Weekly → due_date + 7 days
        as-needed → raises ValueError (not a recurring task)
        """
        if self.frequency == "as-needed":
            raise ValueError(f"'{self.title}' is not a recurring task.")
        base = self.due_date or date.today()
        delta = timedelta(days=1) if self.frequency == "daily" else timedelta(weeks=1)
        return replace(self, completed=False, start_time=None, due_date=base + delta)


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
    conflicts: list[str] = field(default_factory=list)

    def display(self) -> str:
        """Return a formatted string of scheduled tasks sorted by start time."""
        if not self.scheduled_tasks:
            return "No tasks scheduled for today."
        # Sort by "HH:MM" string — zero-padded strings sort correctly alphabetically.
        sorted_tasks = sorted(
            self.scheduled_tasks, key=lambda t: t.start_time or "00:00"
        )
        lines = ["--- Daily Plan ---"]
        for task in sorted_tasks:
            time_label = f"[{task.start_time}]" if task.start_time else "[--:--]"
            lines.append(
                f"{time_label} [{task.priority.name}] {task.title} — {task.duration_minutes} min"
            )
        lines.append(f"\nTotal time: {self.total_duration_minutes} min")
        if self.conflicts:
            lines.append("\n⚠ Conflicts detected:")
            for c in self.conflicts:
                lines.append(f"  {c}")
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
    """The scheduling brain. Retrieves, organises, and manages tasks across all pets."""

    def __init__(self, owner: Owner):
        self.owner = owner

    # ------------------------------------------------------------------
    # Core scheduling
    # ------------------------------------------------------------------

    def generate_schedule(self, start_time: str = "08:00", current_date: date = date.today()) -> DailyPlan:
        """Build a daily plan from all pending tasks across every pet.

        Steps:
          1. Collect all incomplete tasks from every pet that are due today.
          2. Sort by priority (highest first) via _filter_by_priority.
          3. Greedily fill the owner's time budget via _fits_in_time.
          4. Assign consecutive HH:MM start times to each selected task.
          5. Record reasoning for included and skipped tasks.
          6. Run conflict detection and attach any warnings to the plan.
        """
        plan = DailyPlan()
        budget = self.owner.get_available_time()

        pending = [t for t in self.owner.get_all_tasks() if not t.completed and (t.due_date is None or t.due_date <= current_date)]
        sorted_tasks = self._filter_by_priority(pending)
        selected, skipped = self._fits_in_time(sorted_tasks, budget)

        # Assign start times sequentially starting from start_time.
        current_minutes = self._time_to_minutes(start_time)
        for task in selected:
            task.start_time = self._minutes_to_time(current_minutes)
            current_minutes += task.duration_minutes
            plan.scheduled_tasks.append(task)
            plan.total_duration_minutes += task.duration_minutes
            plan.reasoning.append(
                f"'{task.title}' — {task.priority.name} priority, "
                f"{task.duration_minutes} min, starts {task.start_time}"
            )

        for task in skipped:
            plan.skipped_tasks.append(task)
            plan.skipped_reasons.append(
                f"'{task.title}' — needs {task.duration_minutes} min, not enough time remaining"
            )

        plan.conflicts = self.detect_conflicts(plan.scheduled_tasks)
        return plan

    # ------------------------------------------------------------------
    # Sorting and filtering
    # ------------------------------------------------------------------

    def _filter_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted from highest to lowest priority, then by shortest duration first for better time packing."""
        return sorted(tasks, key=lambda t: (-t.priority.value, t.duration_minutes))

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

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> list[Task]:
        """Return tasks filtered by pet name and/or completion status.

        Both filters are optional and can be combined.
        Uses a lambda key when sorting results by start_time ("HH:MM").
        """
        results: list[Task] = []
        for pet in self.owner.pets:
            if pet_name is not None and pet.name != pet_name:
                continue
            for task in pet.tasks:
                if completed is not None and task.completed != completed:
                    continue
                results.append(task)

        # Sort results by start_time if any are set; tasks without a time float to the top.
        return sorted(results, key=lambda t: t.start_time or "00:00")

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Detect overlapping tasks and return warning strings.

        Strategy: for every pair of tasks that both have a start_time, check
        whether their time windows overlap. Returns warnings instead of raising
        exceptions so the schedule is still usable.
        """
        warnings: list[str] = []
        timed = [t for t in tasks if t.start_time is not None]
        for i, a in enumerate(timed):
            a_start = self._time_to_minutes(a.start_time)
            a_end = a_start + a.duration_minutes
            for b in timed[i + 1:]:
                b_start = self._time_to_minutes(b.start_time)
                b_end = b_start + b.duration_minutes
                if a_start < b_end and b_start < a_end:
                    warnings.append(
                        f"'{a.title}' ({a.start_time}–{self._minutes_to_time(a_end)}) "
                        f"overlaps '{b.title}' ({b.start_time}–{self._minutes_to_time(b_end)})"
                    )
        return warnings

    # ------------------------------------------------------------------
    # Task lifecycle helpers
    # ------------------------------------------------------------------

    def mark_task_complete(self, title: str) -> Optional[Task]:
        """Mark the first matching incomplete task as complete.

        If the task is recurring (daily/weekly), automatically adds the next
        occurrence to the same pet's task list using timedelta.
        Returns the newly spawned Task, or None if not recurring.
        """
        for pet in self.owner.pets:
            for task in pet.tasks:
                if task.title == title and not task.completed:
                    task.mark_complete()
                    if task.frequency in ("daily", "weekly"):
                        next_task = task.spawn_next_occurrence()
                        pet.add_task(next_task)
                        return next_task
                    return None
        return None

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

    # ------------------------------------------------------------------
    # Time conversion helpers
    # ------------------------------------------------------------------

    def _time_to_minutes(self, time_str: str) -> int:
        """Convert 'HH:MM' string to total minutes since midnight."""
        h, m = time_str.split(":")
        return int(h) * 60 + int(m)

    def _minutes_to_time(self, minutes: int) -> str:
        """Convert total minutes since midnight to 'HH:MM' string."""
        return f"{minutes // 60:02d}:{minutes % 60:02d}"
