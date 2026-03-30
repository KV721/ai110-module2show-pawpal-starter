from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Priority, Scheduler


# ---------------------------------------------------------------------------
# Helpers — build a minimal owner+pet+scheduler without repeating boilerplate
# ---------------------------------------------------------------------------

def make_task(title="Walk", duration=10, priority=Priority.MEDIUM, frequency="daily", due_date=None):
    return Task(
        title=title,
        description="",
        duration_minutes=duration,
        priority=priority,
        frequency=frequency,
        due_date=due_date,
    )

def make_scheduler(tasks: list, available_minutes=60):
    pet = Pet(name="Mochi", species="dog", age=3)
    for t in tasks:
        pet.add_task(t)
    owner = Owner(name="Jordan", available_minutes=available_minutes, pets=[pet])
    return Scheduler(owner=owner), pet


# ---------------------------------------------------------------------------
# Existing tests (preserved)
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    task = make_task()
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog", age=3)
    assert len(pet.tasks) == 0
    pet.add_task(make_task())
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Happy path 1: schedule respects the time budget
# ---------------------------------------------------------------------------

def test_schedule_respects_time_budget():
    """Tasks whose cumulative duration exceeds the budget should be skipped."""
    tasks = [
        make_task("Walk",    duration=30, priority=Priority.HIGH),
        make_task("Feeding", duration=10, priority=Priority.HIGH),
        make_task("Bath",    duration=30, priority=Priority.LOW),   # won't fit
    ]
    scheduler, _ = make_scheduler(tasks, available_minutes=45)
    plan = scheduler.generate_schedule()

    assert plan.total_duration_minutes <= 45
    scheduled_titles = [t.title for t in plan.scheduled_tasks]
    assert "Walk" in scheduled_titles
    assert "Feeding" in scheduled_titles
    assert "Bath" not in scheduled_titles
    assert any("Bath" in r for r in plan.skipped_reasons)


# ---------------------------------------------------------------------------
# Happy path 2: priority ordering — HIGH comes before MEDIUM before LOW
# ---------------------------------------------------------------------------

def test_priority_ordering_in_schedule():
    """Higher-priority tasks should appear before lower-priority ones."""
    tasks = [
        make_task("Low task",    duration=5, priority=Priority.LOW),
        make_task("High task",   duration=5, priority=Priority.HIGH),
        make_task("Medium task", duration=5, priority=Priority.MEDIUM),
    ]
    scheduler, _ = make_scheduler(tasks, available_minutes=60)
    plan = scheduler.generate_schedule()

    titles = [t.title for t in plan.scheduled_tasks]
    assert titles.index("High task") < titles.index("Medium task")
    assert titles.index("Medium task") < titles.index("Low task")


# ---------------------------------------------------------------------------
# Happy path 3: recurring daily task spawns correct next due_date
# ---------------------------------------------------------------------------

def test_daily_recurring_task_spawns_next_day():
    """Completing a daily task should add a new instance due tomorrow."""
    today = date.today()
    task = make_task("Breakfast", frequency="daily", due_date=today)
    scheduler, pet = make_scheduler([task])

    next_task = scheduler.mark_task_complete("Breakfast")

    # Original task is marked complete
    assert pet.tasks[0].completed is True
    # A new task was appended
    assert len(pet.tasks) == 2
    # New task is due tomorrow
    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False


# ---------------------------------------------------------------------------
# Edge case 4: owner with no tasks → empty plan, no crash
# ---------------------------------------------------------------------------

def test_schedule_with_no_tasks_is_empty():
    """An owner who has no tasks should get an empty plan without errors."""
    owner = Owner(name="Jordan", available_minutes=60)
    scheduler = Scheduler(owner=owner)
    plan = scheduler.generate_schedule()

    assert plan.scheduled_tasks == []
    assert plan.total_duration_minutes == 0
    assert plan.conflicts == []
    assert "No tasks scheduled" in plan.display()


# ---------------------------------------------------------------------------
# Edge case 5: two tasks at the exact same start_time → conflict warning
# ---------------------------------------------------------------------------

def test_conflict_detected_for_same_start_time():
    """Two tasks assigned the same start_time should produce a conflict warning."""
    task_a = make_task("Walk",    duration=30)
    task_b = make_task("Feeding", duration=10)
    task_a.start_time = "08:00"
    task_b.start_time = "08:00"   # exact same start → guaranteed overlap

    owner = Owner(name="Jordan", available_minutes=60)
    scheduler = Scheduler(owner=owner)
    conflicts = scheduler.detect_conflicts([task_a, task_b])

    assert len(conflicts) == 1
    assert "Walk" in conflicts[0]
    assert "Feeding" in conflicts[0]


# ---------------------------------------------------------------------------
# Edge case bonus: as-needed task does NOT spawn a next occurrence
# ---------------------------------------------------------------------------

def test_as_needed_task_does_not_recur():
    """Completing an as-needed task should not create a follow-up instance."""
    task = make_task("Vet visit", frequency="as-needed")
    scheduler, pet = make_scheduler([task])

    result = scheduler.mark_task_complete("Vet visit")

    assert result is None          # no next occurrence returned
    assert len(pet.tasks) == 1     # no new task appended
    assert pet.tasks[0].completed is True
