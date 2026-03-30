import streamlit as st
from pawpal_system import Owner, Pet, Task, Priority, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state vault — check before creating any new objects
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

# ---------------------------------------------------------------------------
# Section 1 — Owner + first pet
# ---------------------------------------------------------------------------
st.header("1. Owner & Pet Info")

with st.form("owner_form"):
    owner_name = st.text_input("Owner name", value="Jordan")
    available_minutes = st.number_input(
        "Time available today (minutes)", min_value=5, max_value=480, value=60
    )
    preferences = st.text_input("Preferences (optional)", value="mornings only")
    st.markdown("**Add your first pet**")
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)
    submitted = st.form_submit_button("Save owner & pet")

if submitted:
    pet = Pet(name=pet_name, species=species, age=int(age))
    owner = Owner(
        name=owner_name,
        available_minutes=int(available_minutes),
        preferences=preferences,
    )
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.success(f"Saved! {owner.name} owns {pet.get_label()}.")

# ---------------------------------------------------------------------------
# Everything below only renders once an Owner exists in the vault
# ---------------------------------------------------------------------------
if st.session_state.owner:
    owner = st.session_state.owner
    scheduler = Scheduler(owner=owner)

    # -----------------------------------------------------------------------
    # Section 2 — Add more pets
    # -----------------------------------------------------------------------
    st.header("2. Add Another Pet")
    with st.form("add_pet_form"):
        new_pet_name = st.text_input("Pet name")
        new_species = st.selectbox("Species", ["dog", "cat", "other"], key="new_species")
        new_age = st.number_input("Age (years)", min_value=0, max_value=30, value=1, key="new_age")
        add_pet_btn = st.form_submit_button("Add pet")

    if add_pet_btn and new_pet_name.strip():
        new_pet = Pet(name=new_pet_name.strip(), species=new_species, age=int(new_age))
        owner.add_pet(new_pet)
        st.success(f"Added {new_pet.get_label()} to {owner.name}'s roster.")

    if owner.pets:
        st.markdown("**Current pets:** " + ", ".join(p.get_label() for p in owner.pets))

    # -----------------------------------------------------------------------
    # Section 3 — Add a task
    # -----------------------------------------------------------------------
    st.header("3. Add a Task")
    pet_names = [p.name for p in owner.pets]

    with st.form("task_form"):
        target_pet = st.selectbox("Assign to pet", pet_names)
        task_title = st.text_input("Task title", value="Morning walk")
        task_desc = st.text_input("Description", value="Walk around the block")
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        priority_str = st.selectbox("Priority", ["HIGH", "MEDIUM", "LOW"])
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
        add_task_btn = st.form_submit_button("Add task")

    if add_task_btn:
        task = Task(
            title=task_title,
            description=task_desc,
            duration_minutes=int(duration),
            priority=Priority[priority_str],
            frequency=frequency,
        )
        for pet in owner.pets:
            if pet.name == target_pet:
                pet.add_task(task)
                st.success(f"Added '{task.title}' to {pet.name}'s tasks.")
                break

    # -----------------------------------------------------------------------
    # Section 4 — Filter & view tasks
    # -----------------------------------------------------------------------
    st.header("4. View & Filter Tasks")
    col1, col2 = st.columns(2)
    with col1:
        filter_pet = st.selectbox("Filter by pet", ["All"] + pet_names, key="filter_pet")
    with col2:
        filter_status = st.selectbox(
            "Filter by status", ["All", "Pending", "Completed"], key="filter_status"
        )

    pet_name_arg = None if filter_pet == "All" else filter_pet
    completed_arg = None
    if filter_status == "Pending":
        completed_arg = False
    elif filter_status == "Completed":
        completed_arg = True

    # filter_tasks() uses a lambda to sort results by start_time "HH:MM"
    filtered = scheduler.filter_tasks(pet_name=pet_name_arg, completed=completed_arg)

    if filtered:
        st.table([
            {
                "Pet": next((p.name for p in owner.pets if task in p.tasks), "?"),
                "Start": task.start_time or "—",
                "Task": task.title,
                "Duration (min)": task.duration_minutes,
                "Priority": task.priority.name,
                "Frequency": task.frequency,
                "Done": task.completed,
            }
            for task in filtered
        ])
    else:
        st.info("No tasks match the selected filters.")

    # -----------------------------------------------------------------------
    # Section 5 — Mark a task complete (with recurring support)
    # -----------------------------------------------------------------------
    st.header("5. Mark Task Complete")
    incomplete = [t for t in owner.get_all_tasks() if not t.completed]
    if incomplete:
        with st.form("complete_form"):
            task_to_complete = st.selectbox(
                "Select task", [t.title for t in incomplete], key="complete_select"
            )
            complete_btn = st.form_submit_button("Mark complete")

        if complete_btn:
            next_occurrence = scheduler.mark_task_complete(task_to_complete)
            st.success(f"'{task_to_complete}' marked complete.")
            if next_occurrence:
                st.info(
                    f"Recurring task detected — next occurrence of "
                    f"'{next_occurrence.title}' added for {next_occurrence.due_date}."
                )
    else:
        st.info("All tasks are complete!")

    # -----------------------------------------------------------------------
    # Section 6 — Generate schedule
    # -----------------------------------------------------------------------
    st.header("6. Generate Today's Schedule")
    start_hour = st.text_input("Schedule start time (HH:MM)", value="08:00")
    st.caption(f"Budget: {owner.available_minutes} min | Preferences: {owner.preferences or 'none'}")

    if st.button("Generate schedule"):
        if not owner.get_all_tasks():
            st.warning("Add at least one task before generating a schedule.")
        else:
            plan = scheduler.generate_schedule(start_time=start_hour)
            st.subheader("Today's Plan")
            st.text(plan.display())
            with st.expander("Why this plan?"):
                st.text(plan.explain())
            if plan.conflicts:
                st.error("Scheduling conflicts detected:")
                for c in plan.conflicts:
                    st.warning(c)
