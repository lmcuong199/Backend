from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Exercise
from app.schemas import ExerciseOut

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=list[ExerciseOut])
def list_exercises(
    category: str | None = Query(default=None, description="cardio / strength / flexibility"),
    muscle_group: str | None = Query(default=None, description="chest / back / legs / ..."),
    search: str | None = Query(default=None, description="match part of the name"),
    db: Session = Depends(get_db),
):
    query = db.query(Exercise)

    if category is not None:
        query = query.filter(Exercise.category == category)
    if muscle_group is not None:
        query = query.filter(Exercise.muscle_group == muscle_group)
    if search is not None:
        query = query.filter(Exercise.name.ilike(f"%{search}%"))

    return query.order_by(Exercise.name).all()


@router.get("/{exercise_id}", response_model=ExerciseOut)
def get_exercise(exercise_id: int, db: Session = Depends(get_db)):
    exercise = db.get(Exercise, exercise_id)
    if exercise is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exercise not found")
    return exercise
