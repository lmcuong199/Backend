from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    # __tablename__ is the real SQL name. The Python class name is just for your code
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # unique=True on email prevents 2 accounts with same address
    # nullable=False = SQL NOT NULL.
    # The database itself rejects a missing value - a safety net underneath Pydantic's validation 
    # index=True builds a lookup structure so searching that column is fast
    # Rule of thumb: index what you filter or sort by
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    # default=utcnow: passes the func itself, not utcnow()
    # SQLAlchemy calls it at insert time, so each row gets its own timestamp
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    # relationship(...) is a pure Python convenience with no SQL column behind it
    # It gives you workout.user and user.workouts so you can navigate objects instead of writing joins by hand
    # back_populates links the 2 sides so they stay sync in memory
    # cascade="all, delete-orphan" is the ORM-level twin of ondelete: remove an entry from workout.entries in Python and its row gets deleted
    workouts = relationship("Workout", back_populates="user", cascade="all, delete-orphan")


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False, default="")
    category = Column(String, nullable=False, index=True)      # cardio / strength / flexibility
    muscle_group = Column(String, nullable=False, index=True)  # chest / back / legs / ...


class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    # ForeignKey("users.id") points at a column in another table and guarantees the target row exists
    # ondelete="CASCADE" means deleting a user deletes their workouts, instead of leaving orphaned rows pointing at a ghost
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    name = Column(String, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    status = Column(String, nullable=False, default="pending", index=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="workouts")
    entries = relationship(
        "WorkoutExercise",
        back_populates="workout",
        cascade="all, delete-orphan",
        # workout.entries always comes back in the order the user arranged the exercises
        order_by="WorkoutExercise.position",
    )


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"
    __table_args__ = (UniqueConstraint("workout_id", "exercise_id", "position"),)

    id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False, index=True)
    sets = Column(Integer, nullable=False, default=1)
    reps = Column(Integer, nullable=False, default=1)
    weight = Column(Float, nullable=True)
    position = Column(Integer, nullable=False, default=0)

    workout = relationship("Workout", back_populates="entries")
    exercise = relationship("Exercise")
