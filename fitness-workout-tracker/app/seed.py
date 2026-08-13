from app.database import Base, SessionLocal, engine
from app.models import Exercise

EXERCISES = [
    # --- strength: chest ---
    {"name": "Bench Press", "category": "strength", "muscle_group": "chest",
     "description": "Barbell press from a flat bench."},
    {"name": "Push-Up", "category": "strength", "muscle_group": "chest",
     "description": "Bodyweight press from the floor."},
    {"name": "Incline Dumbbell Press", "category": "strength", "muscle_group": "chest",
     "description": "Dumbbell press on an inclined bench, targets upper chest."},

    # --- strength: back ---
    {"name": "Pull-Up", "category": "strength", "muscle_group": "back",
     "description": "Bodyweight pull to a bar with an overhand grip."},
    {"name": "Barbell Row", "category": "strength", "muscle_group": "back",
     "description": "Bent-over row pulling a barbell to the waist."},
    {"name": "Deadlift", "category": "strength", "muscle_group": "back",
     "description": "Lift a loaded barbell from the floor to hip height."},

    # --- strength: legs ---
    {"name": "Squat", "category": "strength", "muscle_group": "legs",
     "description": "Barbell back squat to parallel or below."},
    {"name": "Lunge", "category": "strength", "muscle_group": "legs",
     "description": "Step forward and lower the back knee toward the floor."},
    {"name": "Leg Press", "category": "strength", "muscle_group": "legs",
     "description": "Press a weighted sled away with the legs on a machine."},

    # --- strength: shoulders / arms ---
    {"name": "Overhead Press", "category": "strength", "muscle_group": "shoulders",
     "description": "Press a barbell overhead from the front rack."},
    {"name": "Lateral Raise", "category": "strength", "muscle_group": "shoulders",
     "description": "Raise dumbbells out to the sides to shoulder height."},
    {"name": "Bicep Curl", "category": "strength", "muscle_group": "arms",
     "description": "Curl a dumbbell or barbell toward the shoulder."},
    {"name": "Tricep Dip", "category": "strength", "muscle_group": "arms",
     "description": "Lower and press the body between parallel bars."},

    # --- strength: core ---
    {"name": "Plank", "category": "strength", "muscle_group": "core",
     "description": "Hold a straight-body position on forearms and toes."},
    {"name": "Crunch", "category": "strength", "muscle_group": "core",
     "description": "Curl the upper spine off the floor from lying."},

    # --- cardio ---
    {"name": "Running", "category": "cardio", "muscle_group": "full_body",
     "description": "Steady-state or interval running, outdoors or treadmill."},
    {"name": "Cycling", "category": "cardio", "muscle_group": "legs",
     "description": "Road bike or stationary bike at a sustained effort."},
    {"name": "Jump Rope", "category": "cardio", "muscle_group": "full_body",
     "description": "Continuous skipping for conditioning and footwork."},
    {"name": "Rowing Machine", "category": "cardio", "muscle_group": "full_body",
     "description": "Full-body pull on an erg, driving with the legs."},

    # --- flexibility ---
    {"name": "Hamstring Stretch", "category": "flexibility", "muscle_group": "legs",
     "description": "Seated or standing forward fold to lengthen the hamstrings."},
    {"name": "Shoulder Stretch", "category": "flexibility", "muscle_group": "shoulders",
     "description": "Cross-body arm pull to open the rear shoulder."},
    {"name": "Cat-Cow Stretch", "category": "flexibility", "muscle_group": "back",
     "description": "Alternate spinal flexion and extension on all fours."},
]


def seed_exercises(db):
    # Insert any exercise that isn't in the database yet. Safe to run repeatedly.
    # for (name,) in ... returns a list of row tuples: [('Squat',), ('Plank',)], not ['Squat', 'Plank']
    # {} builds a set, not a list
    existing_names = {name for (name,) in db.query(Exercise.name).all()}

    new_rows = [
        # ** splats a dictionary into keyword arguments
        Exercise(**data)
        for data in EXERCISES
        if data["name"] not in existing_names
    ]

    # early exit avoids committing an empty transaction
    if not new_rows:
        return 0

    # all_all stages the objects in the session
    db.add_all(new_rows)
    # commit opens a transaction, writes everything, and makes it permanent
    db.commit()
    return len(new_rows)


def main():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        added = seed_exercises(db)
        total = db.query(Exercise).count()
        print(f"Seeded {added} new exercise(s). Catalogue now has {total}.")
    finally:
        db.close()

# only run main() when this file is executed directly, not when it's imported
if __name__ == "__main__":
    main()
