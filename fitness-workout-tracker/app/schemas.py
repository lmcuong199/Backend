# This file defines the shapes of the data moving in and out of your API
# In FastAPI these are called schemas, and they do three jobs at once: 
# validate incoming data, 
# document your API automatically, 
# and control what goes back out
# ----------------------------------------------------------------------

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Literal

# a class here is just a template describing a kind of data
# inheriting from BaseModel is what makes Pydantic take over
class UserCreate(BaseModel):
    email: EmailStr
    # Field() adds rules beyond the type 
    password: str = Field(min_length=8, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    # from_attributes=True says "you may also read from object attributes"
    # without it you'd get a validation error trying to convert a database row
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime

# This is what you return after a successful login - the JWT from create_access_token
class Token(BaseModel):
    access_token: str
    # bearer means whoever bears this token gets access - no further proof required 
    token_type: str = "bearer"

# the only values `status` may ever hold - anything else is a 422
WorkoutStatus = Literal["pending", "completed", "cancelled"]


class ExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    category: str
    muscle_group: str


class WorkoutEntryCreate(BaseModel):
    """One line of a workout: 'Bench Press, 3 sets x 8 reps @ 60kg'."""

    exercise_id: int
    # ge: greater than or equal
    # le: less than or equal
    sets: int = Field(default=1, ge=1, le=100)
    reps: int = Field(default=1, ge=1, le=1000)
    weight: float | None = Field(default=None, ge=0, le=1000)


class WorkoutEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exercise_id: int
    sets: int
    reps: int
    weight: float | None
    position: int
    exercise: ExerciseOut          # the full exercise, nested


class WorkoutCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    scheduled_at: datetime | None = None
    comment: str | None = None
    # min_length = minimum number of items 
    # rejects an empty workout
    entries: list[WorkoutEntryCreate] = Field(min_length=1)


class WorkoutUpdate(BaseModel):
    """Every field optional - this is a PATCH, so you send only what changes."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    scheduled_at: datetime | None = None
    comment: str | None = None
    status: WorkoutStatus | None = None
    entries: list[WorkoutEntryCreate] | None = None


class WorkoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    scheduled_at: datetime | None
    status: str
    comment: str | None
    created_at: datetime
    entries: list[WorkoutEntryOut]
