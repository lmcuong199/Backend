from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
# func is the gateway to SQL functions: func.count(...) becomes SQL COUNT(...)
# COUNT: how many rows
# SUM: add a column up
# MIN/ MAX: smallest and largest
# COALESCE(a, b): use "a", but if it's NULL, use "b" instead
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Exercise, User, Workout, WorkoutExercise
from app.schemas import (
    ExerciseStat, ProgressPoint, ProgressReport, StatusBreakdown, SummaryReport,
)

router = APIRouter(prefix="/reports", tags=["reports"])

# reusable SQL expressions - defined once, used in several queries
PERFORMED_AT = func.coalesce(Workout.scheduled_at, Workout.created_at)
VOLUME = WorkoutExercise.sets * WorkoutExercise.reps * func.coalesce(WorkoutExercise.weight, 0.0)
TOTAL_REPS = WorkoutExercise.sets * WorkoutExercise.reps


def _scope(user, date_from, date_to, completed_only=True):
    """The filter conditions every report shares: this user, optional date window."""
    conds = [Workout.user_id == user.id]
    if completed_only:
        conds.append(Workout.status == "completed")
    if date_from is not None:
        conds.append(PERFORMED_AT >= date_from)
    if date_to is not None:
        conds.append(PERFORMED_AT <= date_to)
    return conds


@router.get("/summary", response_model=SummaryReport)
def summary(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    all_conds = _scope(current_user, date_from, date_to, completed_only=False)

    counts = dict(
        db.query(Workout.status, func.count(Workout.id))
        .filter(*all_conds)
        .group_by(Workout.status)
        .all()
    )

    done_conds = _scope(current_user, date_from, date_to, completed_only=True)

    sets_sum, reps_sum, volume_sum = (
        db.query(
            func.coalesce(func.sum(WorkoutExercise.sets), 0),
            func.coalesce(func.sum(TOTAL_REPS), 0),
            func.coalesce(func.sum(VOLUME), 0.0),
        )
        .join(Workout, Workout.id == WorkoutExercise.workout_id)
        .filter(*done_conds)
        .one()
    )

    first_at, last_at = (
        db.query(func.min(PERFORMED_AT), func.max(PERFORMED_AT))
        .filter(*done_conds)
        .one()
    )

    return SummaryReport(
        total_workouts=sum(counts.values()),
        by_status=StatusBreakdown(**counts),
        total_sets=sets_sum,
        total_reps=reps_sum,
        total_volume=round(volume_sum, 2),
        first_workout_at=first_at,
        last_workout_at=last_at,
    )


@router.get("/exercises", response_model=list[ExerciseStat])
def per_exercise(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(
            Exercise.id,
            Exercise.name,
            func.count(func.distinct(Workout.id)),
            func.sum(WorkoutExercise.sets),
            func.sum(TOTAL_REPS),
            func.sum(VOLUME),
            func.max(WorkoutExercise.weight),
        )
        .join(WorkoutExercise, WorkoutExercise.exercise_id == Exercise.id)
        .join(Workout, Workout.id == WorkoutExercise.workout_id)
        .filter(*_scope(current_user, date_from, date_to))
        .group_by(Exercise.id, Exercise.name)
        .order_by(func.sum(VOLUME).desc())
        .all()
    )

    return [
        ExerciseStat(
            exercise_id=r[0],
            exercise_name=r[1],
            times_performed=r[2],
            total_sets=r[3],
            total_reps=r[4],
            total_volume=round(r[5], 2),
            max_weight=r[6],
        )
        for r in rows
    ]


@router.get("/progress/{exercise_id}", response_model=ProgressReport)
def progress(
    exercise_id: int,
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exercise = db.get(Exercise, exercise_id)
    if exercise is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exercise not found")

    rows = (
        db.query(
            Workout.id,
            Workout.name,
            PERFORMED_AT,
            WorkoutExercise.sets,
            WorkoutExercise.reps,
            WorkoutExercise.weight,
            VOLUME,
        )
        .join(WorkoutExercise, WorkoutExercise.workout_id == Workout.id)
        .filter(
            *_scope(current_user, date_from, date_to),
            WorkoutExercise.exercise_id == exercise_id,
        )
        .order_by(PERFORMED_AT.asc(), Workout.id.asc())
        .all()
    )

    points = [
        ProgressPoint(
            workout_id=r[0], workout_name=r[1], performed_at=r[2],
            sets=r[3], reps=r[4], weight=r[5], volume=round(r[6], 2),
        )
        for r in rows
    ]

    change = None
    if len(points) >= 2 and points[0].volume > 0:
        change = round((points[-1].volume - points[0].volume) / points[0].volume * 100, 1)

    weights = [p.weight for p in points if p.weight is not None]

    return ProgressReport(
        exercise_id=exercise.id,
        exercise_name=exercise.name,
        points=points,
        max_weight=max(weights) if weights else None,
        volume_change_pct=change,
    )
