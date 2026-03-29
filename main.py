from pawpal_system import Owner, Pet, Task, Priority, Scheduler


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
))
mochi.add_task(Task(
    title="Breakfast",
    description="One cup of dry kibble",
    duration_minutes=5,
    priority=Priority.HIGH,
    frequency="daily",
))
mochi.add_task(Task(
    title="Enrichment puzzle",
    description="Hide treats in the snuffle mat",
    duration_minutes=15,
    priority=Priority.MEDIUM,
    frequency="daily",
))

# --- Tasks for Luna ---
luna.add_task(Task(
    title="Brush coat",
    description="Comb through fur to reduce shedding",
    duration_minutes=10,
    priority=Priority.MEDIUM,
    frequency="weekly",
))
luna.add_task(Task(
    title="Medication",
    description="Half a tablet hidden in a treat",
    duration_minutes=5,
    priority=Priority.HIGH,
    frequency="daily",
))

# --- Owner ---
jordan = Owner(name="Jordan", available_minutes=60, preferences="mornings only")
jordan.add_pet(mochi)
jordan.add_pet(luna)

# --- Schedule ---
scheduler = Scheduler(owner=jordan)
plan = scheduler.generate_schedule()

print("=" * 40)
print("       Today's Schedule for Jordan")
print("=" * 40)
print(plan.display())
print()
print(plan.explain())
print("=" * 40)
