from pawpal_system import Owner, Pet, Task, Priority, Scheduler
from datetime import date


# --- Pets ---
mochi = Pet(name="Mochi", species="dog", age=3)
luna = Pet(name="Luna", species="cat", age=5)

# --- Tasks for Mochi ---
mochi.add_task(Task(
    title="Morning walk",
    description="30-minute walk around the block",
    duration_minutes=30,
    priority=Priority.HIGH,
    frequency="daily",
    due_date=date.today()
))
mochi.add_task(Task(
    title="Breakfast",
    description="One cup of dry kibble",
    duration_minutes=5,
    priority=Priority.HIGH,
    frequency="daily",
    due_date=date.today()
))
mochi.add_task(Task(
    title="Enrichment puzzle",
    description="Hide treats in the snuffle mat",
    duration_minutes=15,
    priority=Priority.MEDIUM,
    frequency="daily",
    due_date=date.today()
))

# --- Tasks for Luna ---
luna.add_task(Task(
    title="Brush coat",
    description="Comb through fur to reduce shedding",
    duration_minutes=10,
    priority=Priority.MEDIUM,
    frequency="weekly",
    due_date=date.today()
))
luna.add_task(Task(
    title="Medication",
    description="Half a tablet hidden in a treat",
    duration_minutes=5,
    priority=Priority.HIGH,
    frequency="daily",
    due_date=date.today()
))

# --- Owner ---
jordan = Owner(name="Jordan", available_minutes=60, preferences="mornings only")
jordan.add_pet(mochi)
jordan.add_pet(luna)

scheduler = Scheduler(owner=jordan)

# ------------------------------------------------------------------
# 1. Generate and display the daily schedule (with start times)
# ------------------------------------------------------------------
plan = scheduler.generate_schedule(start_time="08:00")

print("=" * 45)
print("        Today's Schedule for Jordan")
print("=" * 45)
print(plan.display())
print()
print(plan.explain())

# ------------------------------------------------------------------
# 2. Conflict detection demo
#    Manually set overlapping times on two tasks to trigger a warning.
# ------------------------------------------------------------------
print("\n" + "=" * 45)
print("  Conflict Detection Demo")
print("=" * 45)
mochi.tasks[0].start_time = "08:00"   # Morning walk  08:00–08:30
luna.tasks[1].start_time  = "08:15"   # Medication    08:15–08:20  ← overlaps
conflicts = scheduler.detect_conflicts(jordan.get_all_tasks())
if conflicts:
    for c in conflicts:
        print(f"WARNING: {c}")
else:
    print("No conflicts detected.")

# Reset the manually set time so the rest of the demo is clean.
luna.tasks[1].start_time = None

# ------------------------------------------------------------------
# 3. Filtering demo — pending tasks for Mochi only
# ------------------------------------------------------------------
print("\n" + "=" * 45)
print("  Filter: Mochi's pending tasks")
print("=" * 45)
pending = scheduler.filter_tasks(pet_name="Mochi", completed=False)
for t in pending:
    print(f"  [{t.priority.name}] {t.title} ({t.duration_minutes} min)")

# ------------------------------------------------------------------
# 4. Recurring task demo
#    Complete "Breakfast" (daily) and confirm a new instance is created.
# ------------------------------------------------------------------
print("\n" + "=" * 45)
print("  Recurring Task Demo")
print("=" * 45)
print(f"Mochi's tasks before completing 'Breakfast': {len(mochi.tasks)}")
next_task = scheduler.mark_task_complete("Breakfast")
print(f"Mochi's tasks after  completing 'Breakfast': {len(mochi.tasks)}")
if next_task:
    print(f"  → Next occurrence spawned: '{next_task.title}' due {next_task.due_date}")

print("=" * 45)
