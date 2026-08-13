# This file defines the shapes of the data moving in and out of your API
# In FastAPI these are called schemas, and they do three jobs at once: 
# validate incoming data, 
# document your API automatically, 
# and control what goes back out
# ----------------------------------------------------------------------

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

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
