from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models import Exercise, User, Workout, WorkoutExercise
from app.schemas import WorkoutCreate, WorkoutOut, WorkoutStatus, WorkoutUpdate

router = APIRouter(prefix="/workouts", tags=["workouts"])


def _with_entries(query):
    """Eager-load entries and their exercises, to avoid an N+1 query storm."""
    return query.options(
        selectinload(Workout.entries).selectinload(WorkoutExercise.exercise)
    )


def _get_owned_workout(workout_id: int, db: Session, user: User) -> Workout:
    """Fetch a workout that belongs to this user, or 404. Never leaks other users' data."""
    workout = _with_entries(db.query(Workout)).filter(
        Workout.id == workout_id,
        Workout.user_id == user.id,
    ).first()

    if workout is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workout not found")
    return workout


def _build_entries(db: Session, payloads) -> list[WorkoutExercise]:
    """Turn entry payloads into rows, rejecting any exercise_id that doesn't exist."""
    requested_ids = [entry.exercise_id for entry in payloads]

    found_ids = {
        row[0]
        for row in db.query(Exercise.id).filter(Exercise.id.in_(requested_ids)).all()
    }
    missing = [i for i in dict.fromkeys(requested_ids) if i not in found_ids]
    if missing:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Unknown exercise id(s): {missing}",
        )

    return [
        WorkoutExercise(
            exercise_id=entry.exercise_id,
            sets=entry.sets,
            reps=entry.reps,
            weight=entry.weight,
            position=index,
        )
        for index, entry in enumerate(payloads)
    ]


@router.post("", response_model=WorkoutOut, status_code=status.HTTP_201_CREATED)
def create_workout(
    payload: WorkoutCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workout = Workout(
        # comes from the token, never from the request body
        user_id=current_user.id,
        name=payload.name,
        scheduled_at=payload.scheduled_at,
        comment=payload.comment,
    )
    workout.entries = _build_entries(db, payload.entries)

    db.add(workout)
    db.commit()
    db.refresh(workout)
    return workout


@router.get("", response_model=list[WorkoutOut])
def list_workouts(
    status_filter: WorkoutStatus | None = Query(default=None, alias="status"),
    upcoming_only: bool = Query(default=False, alias="upcoming"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = _with_entries(db.query(Workout)).filter(Workout.user_id == current_user.id)

    if status_filter is not None:
        query = query.filter(Workout.status == status_filter)
    if upcoming_only:
        query = query.filter(Workout.scheduled_at >= datetime.now(timezone.utc))

    return query.order_by(
        Workout.scheduled_at.asc().nullslast(),
        Workout.id.asc(),
    ).all()


@router.get("/{workout_id}", response_model=WorkoutOut)
def get_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_owned_workout(workout_id, db, current_user)


@router.patch("/{workout_id}", response_model=WorkoutOut)
def update_workout(
    workout_id: int,
    payload: WorkoutUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workout = _get_owned_workout(workout_id, db, current_user)
    changes = payload.model_dump(exclude_unset=True)

    if "entries" in changes:
        changes.pop("entries")
        workout.entries = _build_entries(db, payload.entries)

    for field, value in changes.items():
        setattr(workout, field, value)

    db.commit()
    db.refresh(workout)
    return workout


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workout = _get_owned_workout(workout_id, db, current_user)
    db.delete(workout)
    db.commit()
