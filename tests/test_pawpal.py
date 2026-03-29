from pawpal_system import Pet, Task, Priority


def test_mark_complete_changes_status():
    task = Task(
        title="Morning walk",
        description="Walk around the block",
        duration_minutes=30,
        priority=Priority.HIGH,
    )
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog", age=3)
    assert len(pet.tasks) == 0

    pet.add_task(Task(
        title="Breakfast",
        description="One cup of kibble",
        duration_minutes=5,
        priority=Priority.HIGH,
    ))
    assert len(pet.tasks) == 1
